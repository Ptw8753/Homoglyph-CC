# Homoglyph Covert Channel Detector
# Detects potential hidden messages encoded via homoglyph substitution.

import argparse
from pathlib import Path

from Common.homoglyph_file_utils import read_homoglyphs
from Common.regex_preprocesser import get_protected_indices

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_HGY = str(_PROJECT_DIR / "Fonts" / "hgy" / "arial.hgy")

# Read existing homoglyph mappings. Use a project-relative path so detect.py
# can be run from any working directory (the old code used a hardcoded
# "../Fonts/hgy/arial.hgy" that broke unless called from inside Src/).
homoglyphs, char_to_bin = read_homoglyphs(_DEFAULT_HGY)


def extract_bits(text, protected_indices=None):
    """
    Extract binary values from characters that have homoglyph mappings,
    skipping any character index listed in protected_indices.

    protected_indices mirrors the exclusion logic in encode() and decode(),
    ensuring the same set of characters contributes bits here as it does
    in a real encode/decode cycle.
    """
    if protected_indices is None:
        protected_indices = set()

    bits = ""
    for index, char in enumerate(text):
        if char in char_to_bin and index not in protected_indices:
            bits += char_to_bin[char]

    return bits


def decode_bits(bits):
    """
    Convert extracted bits into 7-bit ASCII with no boundary detection.
    Kept as a comparison baseline; prefer decode_bits_with_boundary().
    """
    return "".join(
        chr(int(bits[i:i + 7], 2))
        for i in range(0, len(bits) - 6, 7)
    )


def decode_bits_with_boundary(bits):
    """
    Convert extracted bits into 7-bit ASCII, stopping at the first
    7-bit-aligned all-zero chunk -- the same termination convention
    encode() and decode() use.

    This addresses two of the original TODOs:

    - "Implement message header detection": the protocol has no length
      header, only a trailing all-zero sentinel; recognising that sentinel
      is the closest available equivalent and is what this function does.

    - "Determine message boundaries": trimming at the sentinel separates
      genuine message bytes from the leftover/default homoglyph values
      that follow a real message in the cover text.

    Returns (message, boundary_found). boundary_found is True when an
    actual sentinel chunk was located (versus simply running out of bits),
    since the distinction matters for confidence scoring below.
    """
    trimmed_bits = bits
    boundary_found = False

    for pos in range(7, len(bits) + 1, 7):
        if bits[pos - 7:pos] == "0000000":
            trimmed_bits = bits[:pos - 7]
            boundary_found = True
            break

    message = "".join(
        chr(int(trimmed_bits[i:i + 7], 2))
        for i in range(0, len(trimmed_bits) - 6, 7)
    )
    return message, boundary_found


def analyze_text(text, protected_indices=None):
    """
    Analyse text for characters that have homoglyph mappings, excluding
    any index in protected_indices so the analysis matches what decode()
    would actually consume.
    """
    if protected_indices is None:
        protected_indices = set()

    total_chars = len(text)
    mapped_chars = 0
    suspicious_chars = []

    for index, char in enumerate(text):
        if char in char_to_bin and index not in protected_indices:
            mapped_chars += 1
            suspicious_chars.append({
                "position": index,
                "character": char,
                "binary": char_to_bin[char]
            })

    percentage = (mapped_chars / total_chars * 100) if total_chars > 0 else 0
    return mapped_chars, percentage, suspicious_chars


def compare_cover(original, encoded):
    """
    Compare the original cover text against the encoded text to identify
    characters that were replaced with homoglyphs.
    """
    substitutions = []
    for index, (original_char, encoded_char) in enumerate(zip(original, encoded)):
        if original_char != encoded_char:
            if original_char in homoglyphs and encoded_char in homoglyphs[original_char]:
                substitutions.append({
                    "position": index,
                    "original": original_char,
                    "encoded": encoded_char
                })
    return substitutions


def score_confidence(mapped_chars, percentage, message, boundary_found):
    """
    Combine several independent signals into a single confidence score
    (0–100) and a human-readable label.

    This addresses two more of the original TODOs:

    - "Improve detection accuracy": four independent signals are combined
      so a text must look suspicious on more than one axis before being
      flagged as a likely carrier.

    - "Reduce false positives": the original single hard 80%-printable
      cutoff fired on any mostly-readable text; requiring a *non-trivial*
      boundary AND a plausible decoded length alongside the printable ratio
      eliminates most of those spurious matches.

    Returns (score, label, reasons) where reasons is a list of
    (signal_name, weight_added, explanation) tuples for printing.
    """
    reasons = []
    score = 0.0

    # Signal 1 (up to 25 pts): fraction of characters that have a
    # homoglyph mapping.  Near-zero means there is nothing to analyse.
    if mapped_chars == 0:
        return 0.0, "No channel detected", [
            ("mapped_chars", 0, "No characters with homoglyph mappings found.")
        ]

    # Typical encoded cover text lands around 70%; very low percentages
    # are proportionally weaker evidence.
    mapped_weight = min(25.0, percentage / 3.0)
    score += mapped_weight
    reasons.append((
        "mapped_percentage", round(mapped_weight, 1),
        f"{percentage:.1f}% of non-protected characters have a homoglyph mapping."
    ))

    # Signal 2 (35 pts): was an explicit message boundary found that
    # terminates a *non-empty* decoded run?  Random cover text essentially
    # never contains a clean all-zero 7-bit-aligned chunk right after a
    # plausible-looking run of bytes.  An immediate (empty-message)
    # terminator is much weaker evidence and scores only 5 pts.
    if boundary_found and len(message) > 0:
        score += 35.0
        reasons.append((
            "boundary_found", 35.0,
            "All-zero terminator found after a non-empty decoded run -- "
            "consistent with a deliberately embedded message."
        ))
    elif boundary_found:
        score += 5.0
        reasons.append((
            "boundary_found", 5.0,
            "Terminator found immediately (empty message) -- weak evidence; "
            "common even in unmodified cover text."
        ))
    else:
        reasons.append((
            "boundary_found", 0.0,
            "No terminator found; trailing bytes may be incidental noise."
        ))

    # Signal 3 (up to 30 pts): printable-character ratio of the
    # *boundary-trimmed* message, not the raw decode stream.
    if message:
        printable_ratio = sum(1 for c in message if c.isprintable()) / len(message)
    else:
        printable_ratio = 0.0

    printable_weight = printable_ratio * 30.0
    score += printable_weight
    reasons.append((
        "printable_ratio", round(printable_weight, 1),
        f"{printable_ratio * 100:.1f}% of boundary-trimmed decoded bytes are printable."
    ))

    # Signal 4 (up to 10 pts): decoded message length -- a single
    # printable byte is weak evidence; a multi-word string is strong.
    length_weight = min(10.0, len(message) / 2.0)
    score += length_weight
    reasons.append((
        "message_length", round(length_weight, 1),
        f"Boundary-trimmed decoded message is {len(message)} character(s)."
    ))

    score = min(100.0, score)

    if score >= 70:
        label = "Likely hidden message"
    elif score >= 35:
        label = "Possible hidden message"
    else:
        label = "No confident detection"

    return score, label, reasons


def detect(filepath="out.txt", cover_filepath=None):
    """
    Detect potential homoglyph covert channels in a file.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        text = file.read()

    print("\n===== Homoglyph Covert Channel Detector =====")
    print(f"\nAnalyzing file: {filepath}")

    # Mirror encode()'s and decode()'s exclusion of protected spans so the
    # bits extracted here are the same as the bits those functions consume.
    protected_indices = get_protected_indices(filepath, [" "] + homoglyphs[" "])

    # Character analysis
    mapped_chars, percentage, suspicious = analyze_text(text, protected_indices)

    print("\n--- Character Analysis ---")
    print(f"Total characters: {len(text)}")
    print(f"Characters with homoglyph mappings (outside protected spans): {mapped_chars}")
    print(f"Mapped character percentage: {percentage:.2f}%")

    # Binary extraction
    bits = extract_bits(text, protected_indices)

    print("\n--- Binary Extraction ---")
    print(f"Extracted bits: {len(bits)}")

    # Decoding -- with and without boundary detection so the difference is visible
    raw_message = decode_bits(bits)
    message, boundary_found = decode_bits_with_boundary(bits)

    print("\n--- Potential Hidden Message ---")
    print(f"Boundary-trimmed: {message!r}")
    if raw_message != message:
        print(f"Raw (no boundary trim, for comparison): {raw_message!r}")
    print(f"Message boundary (all-zero terminator) found: {boundary_found}")

    # Confidence scoring
    score, label, reasons = score_confidence(
        mapped_chars, percentage, message, boundary_found
    )

    print("\n--- Detection Results ---")
    print(f"Confidence score: {score:.1f}/100  --  {label}")
    for name, weight, note in reasons:
        print(f"  [{name}] +{weight}: {note}")

    # Optional cover text comparison
    if cover_filepath:
        with open(cover_filepath, "r", encoding="utf-8") as file:
            original_text = file.read()

        substitutions = compare_cover(original_text, text)

        print("\n--- Cover Text Comparison ---")
        print(f"Homoglyph substitutions found: {len(substitutions)}")

        for sub in substitutions:
            print(
                f"Position {sub['position']}: "
                f"'{sub['original']}' -> '{sub['encoded']}'"
            )

        if substitutions:
            print("\nPotential homoglyph covert channel detected.")
        else:
            print("\nNo homoglyph substitutions detected.")

        if len(original_text) != len(text):
            print("\nWarning: Original and encoded texts have different lengths.")

    print("\n===== Analysis Complete =====\n")

    return score, label, message, boundary_found


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect homoglyph covert channels."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="out.txt",
        help="File to analyze (default: out.txt)"
    )
    parser.add_argument(
        "--cover",
        help="Optional original cover text for comparison"
    )
    args = parser.parse_args()
    detect(args.file, args.cover)
