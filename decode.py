from Common.homoglyph_file_utils import read_homoglyphs

homoglyphs, char_to_bin = read_homoglyphs("arial.hgy")


def decode():
    with open("out.txt", "r", encoding="utf-8") as file:
        lines = file.readlines()

    bits = ""

    for line in lines:
        for char in line:
            if char in char_to_bin:
                bits += char_to_bin[char]

    # Only decode complete 7-bit characters.
    out = ''.join(chr(int(bits[i:i + 7], 2))
                  for i in range(0, len(bits) - 6, 7))
    print(out)
    return out


if __name__ == '__main__':
    decode()
