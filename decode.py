# Homoglyph decoder
# TODO implement a message header???
# How will we tell if any message is a homoglyph message?

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