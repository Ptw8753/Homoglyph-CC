# a map from a unicode character to a set of all characters that it is homoglyphic with
import random

from Common.homoglyph_file_utils import read_homoglyphs

# gets a character, homoglyphic to 'char_in', that encodes 'bit_array'
def get_encoded_char(char_in, bit_array, homoglyphs, char_to_bin):
    if len(bit_array) == 0:
        return char_in

    # convert bits to a binary value
    bin = "".join(str(bit) for bit in bit_array)

    homoglyph_chars = homoglyphs[char_in] + [char_in]
    # get all chars that encode bits
    return random.choice([char for char in homoglyph_chars if char_to_bin[char] == bin])

def encode(filepath_in: str, filepath_out: str, font_hgy: str, message: str):
    # preprocess the font
    homoglyphs, char_to_bin = read_homoglyphs(font_hgy)

    bin = list("".join(format(ord(c), "07b") for c in message))

    encoded_text = ""

    with open(filepath_in, "r") as file:
        while char := file.read(1):
            if char in homoglyphs:  # if the given char has a homoglyph
                bit_length = len(char_to_bin[char])  # -2 to cut off the 0b
                bits_to_encode = bin[0:bit_length]
                encoded_text += get_encoded_char(char, bits_to_encode, homoglyphs, char_to_bin)
                bin = bin[bit_length:] # shave these chars from bin

    with open(filepath_out, "w", encoding='utf_8') as file:
        file.write(encoded_text)
