import math
from encodings import utf_8


def write_homoglyphs(homoglyphs: list[list[str]], filepath_out: str):
    with open(filepath_out, "w", encoding='utf_8') as f:
        lines = []
        lines.append(f"{len(homoglyphs)}\n")
        for glyph_set in homoglyphs:
            glyphs = ""
            for glyph in glyph_set:
                glyphs += glyph
            lines.append(glyphs + "\n")
        f.writelines(lines)

def read_homoglyphs(filepath_in: str):
    homoglyphs = dict()
    char_to_bin = dict()

    with open(filepath_in, "r", encoding='utf_8') as f:
        lines = [line.strip("\n") for line in f.readlines()]
        # get total number of homoglyph groups
        num_groups = int(lines[0])
        for i in range(num_groups):
            group = list(lines[i+1])

            # connect all elements of the group
            for g in group:
                homoglyphs[g] = []
                for o_g in group:
                    if o_g != g:
                        homoglyphs[g].append(o_g)

            # wrap characters and assign binary values
            max_binary_value = 2 ** math.floor(math.log2(len(group)))

            for j in range(len(group)):
                # wrap value
                mod_val = j % max_binary_value
                # assign the ith character in the homoglyphs list to a binary value
                char_to_bin[group[j]] = str(bin(mod_val))[2:]

    return homoglyphs, char_to_bin