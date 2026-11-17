# Homoglyph-CC

A covert channel implementation and detector built on Unicode homoglyph
substitution. Developed for the Covert Channels course (RIT).

---

## What is a Homoglyph Covert Channel?

A *covert channel* is a communication path that bypasses a system's security
policy by exploiting shared resources rather than explicit communication
mechanisms (Lampson 1973).

This implementation uses **homoglyphs** — distinct Unicode codepoints that
render as visually identical glyphs in a given font — to embed a secret
bit-stream inside ordinary text. To any reader (or casual automated scanner)
the carrier document looks unchanged; the hidden data is only recoverable
with knowledge of the font's glyph-collision map.

### Example homoglyph groups in Arial Unicode

| Visible glyph | Codepoints in group | Bits encodable |
|---|---|---|
| `A` | U+0041 (Latin), U+0391 (Greek Α), U+0410 (Cyrillic А) | 1 bit |
| `I` | U+0049, U+0399, U+0406, U+04C0, U+2160 | 2 bits |
| ` ` (space) | 23 variants including NBSP, zero-width joiners, en-space, em-space … | 4 bits |
| `o` | U+006F, U+03BF (Greek ο), U+043E (Cyrillic о) | 1 bit |

The encoder scans the cover text character by character. Wherever a
character belongs to a homoglyph group it replaces it with the group member
whose assigned binary value matches the next bits of the secret message.
Characters with no homoglyph (digits, most punctuation, `n`, `t`, …) are
passed through unchanged, so the output has the **same length and visual
appearance** as the original.

---

## Repository layout

```
Homoglyph-CC/
├── Fonts/
│   ├── ttf/          Arial-Unicode.ttf, Comic-Sans.ttf (source fonts)
│   └── hgy/          arial.hgy, comic-sans.hgy  (pre-built glyph-collision maps)
├── Frequency Analysis/
│   ├── tale_of_two_cities.txt    sample plaintext corpus
│   └── tale_of_two_cities.frq   pre-computed character frequencies
├── Src/
│   ├── Common/
│   │   ├── homoglyph_file_utils.py   .hgy read/write + binary assignment
│   │   └── regex_preprocesser.py    URL / e-mail exclusion
│   ├── duplicate_glyph_finder.py    builds a glyph-collision map from a TTF
│   ├── frequency_analyisis.py       estimates channel capacity in bits/char
│   ├── encode.py                    hides a message in a cover text file
│   ├── decode.py                    recovers a message from an encoded file
│   ├── detect.py                    statistical detector with confidence scoring
│   └── runner.py                    end-to-end demo (font → encode → decode)
├── plaintext.txt    sample cover text
├── modified.txt     sample encoded output (produced by runner.py)
└── test_decode.py   unit + integration test suite
```

---

## Requirements

- Python 3.10+
- [fonttools](https://github.com/fonttools/fonttools) — `pip install fonttools`

No other third-party packages are needed.

---

## Quick start

```bash
# Run the full pipeline (font analysis → frequency analysis → encode → decode)
python3 Src/runner.py
```

Expected output:
```
1. Analyzing font at …/Fonts/hgy/arial.hgy
2. Performing frequency analysis on the font
    The analyzed font can encode at 0.7445 bits per char
3. Encoding "This is my secret message!" within the text at plaintext.txt …
4. Decoding from modified.txt
    The decoded secret is "This is my secret message!"
```

```bash
# Encode a custom message
python3 -c "
import sys; sys.path.insert(0,'Src')
from Src.encode import encode
encode('plaintext.txt', 'modified.txt', 'Fonts/hgy/arial.hgy', 'my secret')
"

# Decode it back
python3 -c "
import sys; sys.path.insert(0,'Src')
from Src.decode import decode
print(decode('modified.txt', 'Fonts/hgy/arial.hgy'))
"

# Run the detector
python3 -c "
import sys; sys.path.insert(0,'Src')
from Src.detect import detect
detect('modified.txt', cover_filepath='plaintext.txt')
"

# Run the test suite
python3 -m unittest test_decode -v
```

---

## Channel design

### Glyph-collision map (`.hgy` format)

`duplicate_glyph_finder.py` loads a TTF, hashes each glyph's outline with
SHA-256 (using `fonttools`' `DecomposingRecordingPen` to flatten composites
first), and groups all codepoints that share an outline hash. Groups of size
one (unique glyphs) carry no information and are excluded.

The `.hgy` file stores one group per line; the first line is the group count.
Arial Unicode produces **442 groups** covering 957 unique codepoints.

### Binary assignment

Within a group of *n* characters, the encoder can represent
⌊log₂ *n*⌋ bits per substitution. The first 2^⌊log₂ n⌋ members are assigned
binary values `0 … 2^⌊log₂ n⌋ − 1`; any excess members wrap around and
alias existing values (they are currently unused — see *Future work*).

### Encoding

1. Convert the secret message to a flat list of 7-bit ASCII values, then
   append a 7-bit all-zero terminator so the decoder knows where the message
   ends.
2. Scan the cover text. For each character that belongs to a homoglyph
   group **and** is not inside a protected span (see below), dequeue the
   next ⌊log₂ *n*⌋ bits and substitute the matching group member.
3. All other characters are written to the output unchanged.

A length guard prevents writing any output if the cover text does not have
enough homoglyph-capable characters to hold the full message plus terminator.

### URL and e-mail protection

Substituting inside a URL or e-mail address is fragile (URL normalizers and
mail clients may canonicalize or reject the altered address) and conspicuous
to a reader who hovers over a link. `regex_preprocesser.py` identifies
"word-boundary tokens" that contain a `.` or `@` separator and marks every
character index in those tokens as *protected*. Both `encode()` and
`decode()` skip protected indices, so the sets computed on the original and
encoded text stay in sync.

### Decoding

The decoder mirrors the encoder step by step: it reads the encoded file,
skips protected indices, looks up each character's binary value in
`char_to_bin`, accumulates bits, and stops as soon as the last complete
7-bit window is all zero (the terminator appended by the encoder). The
message is then reconstructed from the trimmed bit-string.

### Channel capacity

On the sample A Tale of Two Cities corpus, Arial Unicode encodes at
**≈ 0.74 bits per character**. The 573-character `plaintext.txt` cover text
(which includes a URL and an e-mail address) provides **408 usable bits**,
enough to hide up to **58 ASCII characters**.

---

## Detector

`detect.py` attempts to identify homoglyph-encoded text *without* access to
the original cover document. It combines four independent signals into a
0–100 confidence score:

| Signal | Max pts | Rationale |
|---|---|---|
| Mapped-character percentage | 25 | Encoded text has ~70% of characters carrying a substitution |
| All-zero terminator found (non-empty) | 35 | Random text essentially never produces a clean 7-bit-aligned zero chunk after a plausible decoded run |
| Printable-character ratio of trimmed message | 30 | Real ASCII messages approach 100% printable |
| Decoded message length | 10 | A 20-character printable string is stronger evidence than a single byte |

Scores ≥ 70 are labelled **"Likely hidden message"**; 35–69 are
**"Possible hidden message"**; below 35 is **"No confident detection"**.

On the sample files: an encoded `modified.txt` scores **~99/100**; the
unmodified `plaintext.txt` scores **~29/100**.

---

## Future work

- **Randomized aliasing** — excess group members (those that wrap around to
  an already-assigned binary value) could be chosen randomly between
  substitutions to flatten the per-character substitution-frequency
  distribution and reduce statistical detectability.
- **Multi-font support** — the Comic Sans `.hgy` is already built; a
  per-document font selector would increase the key space.
- **Regex preprocessor extensions** — add exclusions for inline code spans,
  Markdown links, and other structured markup that should not be altered.
- **Detector robustness** — a chi-squared test on the observed binary-value
  distribution (each value should appear roughly equally often in
  unencoded text; an encoder biased toward certain bits would skew this)
  could complement the current heuristic.

---

## References

Lampson, B. W. (1973). A note on the confinement problem. *Communications of
the ACM*, 16(10), 613–615.
