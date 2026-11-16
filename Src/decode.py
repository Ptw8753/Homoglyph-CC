from Common.homoglyph_file_utils import read_homoglyphs
from Common.regex_preprocesser import get_protected_indices


# takes a modified text file filepath_in and writes the embedded covert message to filepath_out
# assuming the use of font_hgy
def decode(filepath_in: str, font_hgy: str):
    # preprocess the font
    homoglyphs, char_to_bin = read_homoglyphs(font_hgy)

    # first thing to do, preprocess out protected indices
    protected_indices = get_protected_indices(filepath_in, [" "] + homoglyphs[" "])

    bits = ""

    with open(filepath_in, "r", encoding="utf-8") as file:
        index = 0
        while char := file.read(1):
            if char in char_to_bin and index not in protected_indices:
                bits += char_to_bin[char]
                # if the last full 7-byte is all 0, we can return
                if len(bits) >= 7 and bits[len(bits) - (len(bits) % 7) - 7:len(bits) - (len(bits) % 7)] == '0000000':
                    bits = bits[:len(bits) - (len(bits) % 7) - 7]
                    break
            index += 1

    # Only decode complete 7-bit characters.
    out = ''.join(chr(int(bits[i:i + 7], 2))
                  for i in range(0, len(bits) - 6, 7))

    return out
