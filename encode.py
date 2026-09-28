homoglyphs = {
    'a': 'а',
    'A': 'Α',
    'c': 'с',
    'd': 'ԁ',
    'e': 'е',
    'j': 'ј',
    'o': 'ο',
    'p': 'р',
    's': 'ѕ',
    'x': 'х',
    'y': 'у',
}

inverted_homoglyphs = {value: key for key, value in homoglyphs.items()}

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def encode():
    message = 'Secret message'
    bin = list("".join(format(ord(c), "07b") for c in message))

    lines = []

    with open("in.txt", "r") as file:
       lines = file.readlines()

    for line_idx in range(len(lines)):
        line = lines[line_idx]
        for char_idx in range(len(line)):
            if line[char_idx] in homoglyphs:
                if len(bin) > 0:
                    if bin[0] == '1':
                        # write the replacement
                        line = line[:char_idx] + homoglyphs[line[char_idx]] + line[char_idx+1:]
                    # pop the next bit
                    bin = bin[1:]
        lines[line_idx] = line

    with open("out.txt", "w") as file:
        file.writelines(lines)


def decode():
    with open("out.txt", "r") as file:
       lines = file.readlines()

    bits = ""

    for line in lines:
        for char in line:
            if char in homoglyphs:
                bits += '0'
            elif char in inverted_homoglyphs:
                bits += '1'

    out = ''.join(chr(int(bits[i:i + 7], 2)) for i in range(0, len(bits), 7))
    print(out)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    encode()
    decode()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

