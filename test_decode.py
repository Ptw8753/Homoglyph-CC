"""Tests for the homoglyph covert channel: encoding, decoding, regex exclusion, and detection."""

import sys
import tempfile
import unittest
from pathlib import Path

# Ensure both the repo root and Src/ are on the path so imports work
# regardless of which directory the test runner is launched from.
PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "Src"
for _p in (str(PROJECT_DIR), str(SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from Src.Common.homoglyph_file_utils import read_homoglyphs
from Src.Common.regex_preprocesser import get_protected_indices
from Src.encode import encode
from Src.decode import decode
from Src.detect import (
    analyze_text, extract_bits, decode_bits_with_boundary, score_confidence
)

FONT_HGY = str(PROJECT_DIR / "Fonts" / "hgy" / "arial.hgy")
PLAINTEXT = str(PROJECT_DIR / "plaintext.txt")


class TestHomoglyphUtils(unittest.TestCase):

    def test_homoglyph_mapping_loads(self):
        homoglyphs, char_to_bin = read_homoglyphs(FONT_HGY)
        self.assertTrue(homoglyphs)
        self.assertTrue(char_to_bin)

    def test_seven_bit_ascii_conversion(self):
        """Bit packing and unpacking must be a perfect round-trip."""
        message = "Secret message"
        bits = "".join(format(ord(c), "07b") for c in message)
        restored = "".join(
            chr(int(bits[i:i + 7], 2))
            for i in range(0, len(bits) - 6, 7)
        )
        self.assertEqual(restored, message)


class TestEncodeDecodeRoundTrip(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.modified = Path(self.tmpdir.name) / "modified.txt"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_round_trip_full_message(self):
        message = "This is my secret message!"
        encode(PLAINTEXT, str(self.modified), FONT_HGY, message)
        decoded = decode(str(self.modified), FONT_HGY)
        self.assertTrue(decoded.startswith(message))

    def test_round_trip_short_message(self):
        encode(PLAINTEXT, str(self.modified), FONT_HGY, "hi")
        decoded = decode(str(self.modified), FONT_HGY)
        self.assertTrue(decoded.startswith("hi"))

    def test_cover_text_length_preserved(self):
        """encode() must substitute homoglyphs, never drop characters --
        dropping would corrupt the cover text and make the channel visible."""
        encode(PLAINTEXT, str(self.modified), FONT_HGY, "test")
        original = Path(PLAINTEXT).read_text(encoding="utf-8")
        encoded = self.modified.read_text(encoding="utf-8")
        self.assertEqual(len(original), len(encoded))

    def test_only_homoglyphs_substituted(self):
        """Every changed character must be a registered homoglyph of the
        original -- no arbitrary mutations."""
        homoglyphs, _ = read_homoglyphs(FONT_HGY)
        encode(PLAINTEXT, str(self.modified), FONT_HGY, "hi")
        original = Path(PLAINTEXT).read_text(encoding="utf-8")
        encoded = self.modified.read_text(encoding="utf-8")
        for orig_char, enc_char in zip(original, encoded):
            if orig_char != enc_char:
                self.assertIn(orig_char, homoglyphs,
                    f"{orig_char!r} changed to {enc_char!r} but has no homoglyph entry")
                self.assertIn(enc_char, homoglyphs[orig_char] + [orig_char],
                    f"{enc_char!r} is not a known homoglyph of {orig_char!r}")

    def test_message_too_long_does_not_write_output(self):
        """If the message exceeds channel capacity no output file is written."""
        cover = Path(self.tmpdir.name) / "tiny.txt"
        cover.write_text("ab", encoding="utf-8")
        out = Path(self.tmpdir.name) / "out.txt"
        encode(str(cover), str(out), FONT_HGY, "Way too long for two characters of cover")
        self.assertFalse(out.exists(), "encode() should not write output when capacity exceeded")


class TestRegexPreprocesser(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        homoglyphs, _ = read_homoglyphs(FONT_HGY)
        self.whitespace_chars = [" "] + homoglyphs[" "]

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write(self, text):
        p = Path(self.tmpdir.name) / "cover.txt"
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_email_indices_protected(self):
        path = self._write("Contact research@rit.edu for details.")
        protected = get_protected_indices(path, self.whitespace_chars)
        text = Path(path).read_text(encoding="utf-8")
        email_start = text.index("research@rit.edu")
        email_end = email_start + len("research@rit.edu")
        self.assertTrue(any(i in protected for i in range(email_start, email_end)),
            "Email address should be in protected indices")

    def test_url_indices_protected(self):
        path = self._write("Visit www.rit.edu for more info.")
        protected = get_protected_indices(path, self.whitespace_chars)
        text = Path(path).read_text(encoding="utf-8")
        url_start = text.index("www.rit.edu")
        self.assertIn(url_start, protected, "URL should be in protected indices")

    def test_plain_text_has_no_protected_indices(self):
        path = self._write("Just plain text with no links or emails here.")
        protected = get_protected_indices(path, self.whitespace_chars)
        self.assertEqual(len(protected), 0)

    def test_encode_decode_preserves_email_and_url(self):
        """URL and email must survive encoding unchanged, and decode must
        still recover the message."""
        cover_text = (
            "Contact ptw8753@rit.edu or visit www.google.com for the paper. "
            "In computer security a covert channel is used in a type of attack "
            "that creates a capability to transfer information objects between "
            "processes that are not supposed to be allowed to communicate."
        )
        cover = Path(self.tmpdir.name) / "cover.txt"
        out = Path(self.tmpdir.name) / "encoded.txt"
        cover.write_text(cover_text, encoding="utf-8")

        encode(str(cover), str(out), FONT_HGY, "hi")
        encoded = out.read_text(encoding="utf-8")

        self.assertIn("ptw8753@rit.edu", encoded, "Email address must not be altered")
        self.assertIn("www.google.com", encoded, "URL must not be altered")

        decoded = decode(str(out), FONT_HGY)
        self.assertTrue(decoded.startswith("hi"), f"Expected 'hi', got {decoded!r}")


class TestDetect(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.modified = Path(self.tmpdir.name) / "modified.txt"
        homoglyphs, _ = read_homoglyphs(FONT_HGY)
        self.whitespace_chars = [" "] + homoglyphs[" "]

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_encoded_file_scores_as_likely(self):
        encode(PLAINTEXT, str(self.modified), FONT_HGY, "This is my secret message!")
        text = self.modified.read_text(encoding="utf-8")
        protected = get_protected_indices(str(self.modified), self.whitespace_chars)

        mapped_chars, percentage, _ = analyze_text(text, protected)
        bits = extract_bits(text, protected)
        message, boundary_found = decode_bits_with_boundary(bits)
        score, label, _ = score_confidence(mapped_chars, percentage, message, boundary_found)

        self.assertTrue(boundary_found)
        self.assertTrue(message.startswith("This is my secret message!"))
        self.assertGreaterEqual(score, 70)
        self.assertEqual(label, "Likely hidden message")

    def test_clean_cover_text_does_not_score_as_likely(self):
        text = Path(PLAINTEXT).read_text(encoding="utf-8")
        protected = get_protected_indices(PLAINTEXT, self.whitespace_chars)

        mapped_chars, percentage, _ = analyze_text(text, protected)
        bits = extract_bits(text, protected)
        message, boundary_found = decode_bits_with_boundary(bits)
        score, label, _ = score_confidence(mapped_chars, percentage, message, boundary_found)

        self.assertLess(score, 70, f"Clean cover text scored {score:.1f} -- too high")

    def test_boundary_trims_trailing_noise(self):
        """With a short message the trimmed output should be short, not a long
        noise tail."""
        encode(PLAINTEXT, str(self.modified), FONT_HGY, "hi")
        text = self.modified.read_text(encoding="utf-8")
        protected = get_protected_indices(str(self.modified), self.whitespace_chars)
        bits = extract_bits(text, protected)
        message, boundary_found = decode_bits_with_boundary(bits)

        self.assertTrue(boundary_found)
        self.assertTrue(message.startswith("hi"))
        self.assertLess(len(message), 15,
            "Boundary trim should leave a short message, not a long noise tail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
