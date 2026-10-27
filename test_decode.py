"""Basic tests for the existing homoglyph decoder (no encoding changes)."""

import unittest
from pathlib import Path
from unittest.mock import patch

from Common.homoglyph_file_utils import read_homoglyphs
from decode import decode


PROJECT_DIR = Path(__file__).resolve().parent


class TestDecode(unittest.TestCase):
    def test_homoglyph_mapping_loads(self):
        homoglyphs, char_to_bin = read_homoglyphs(str(PROJECT_DIR / "arial.hgy"))
        self.assertTrue(homoglyphs)
        self.assertTrue(char_to_bin)

    def test_seven_bit_ascii_conversion(self):
        message = "Secret message"
        bits = "".join(format(ord(character), "07b") for character in message)
        restored = "".join(
            chr(int(bits[i:i + 7], 2))
            for i in range(0, len(bits) - 6, 7)
        )
        self.assertEqual(restored, message)

    def test_existing_encoded_output(self):
        """The included out.txt should start with the encoder's sample message.

        The current format has no message-length header, so extra decoded
        characters after the message are possible and are not checked here.
        """
        self.assertTrue((PROJECT_DIR / "out.txt").is_file(), "Missing out.txt")
        with patch("builtins.print"):
            result = decode()
        self.assertTrue(
            result.startswith("Secret message"),
            f"Expected sample message at start; got {result!r}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
