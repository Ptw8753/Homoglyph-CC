# a map from a unicode character to a set of all characters that it is homoglyphic with
import random

# TODO these are example values for now, I still need to hook up the analysis dicts here
homoglyphs = {'e': ['1', '2']}

# a map from a unicode character to the binary that it represents
char_to_bin = {'e': '0',
               '1': '1',
               '2': '0'
               }

def character_is_homoglyph(character):
    return character in homoglyphs

# gets a character, homoglyphic to 'char_in', that encodes 'bit_array'
def get_encoded_char(char_in, bit_array):
    # convert bits to a binary value
    bin = "".join(str(bit) for bit in bit_array)

    homoglyph_chars = homoglyphs[char_in] + [char_in]
    # get all chars that encode bits
    return random.choice([char for char in homoglyph_chars if char_to_bin[char] == bin])

def encode():
    message = 'Secret message'
    bin = list("".join(format(ord(c), "07b") for c in message))

    lines = []

    with open("in.txt", "r") as file:
       lines = file.readlines()

    for line_idx in range(len(lines)):
        line = lines[line_idx]
        for char_idx in range(len(line)):
            if character_is_homoglyph(line[char_idx]):
                bit_length = len(char_to_bin[line[char_idx]])
                bits_to_encode = bin[0:bit_length]
                line = line[:char_idx] + get_encoded_char(line[char_idx], bits_to_encode) + line[char_idx+1:]
                # shave these chars from bin
                bin = bin[bit_length:]
        # overwrite the line with the updated one
        lines[line_idx] = line

    with open("out.txt", "w") as file:
        file.writelines(lines)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    encode()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

