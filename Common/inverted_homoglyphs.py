from Common.homoglyph_file_utils import read_homoglyphs

homoglyphs, char_to_bin = read_homoglyphs("Homoglyph-CC/arial.hgy")

inverted_homoglyphs = dict()

for character in char_to_bin:
    inverted_homoglyphs[character] = char_to_bin[character]