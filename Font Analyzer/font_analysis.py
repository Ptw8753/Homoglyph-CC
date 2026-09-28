import math

from Common.homoglyph_file_utils import write_homoglyphs
from font_investigation import get_duplicate_glyphs

# Let's say there are n identical characters. That means that we can use that glyph to represent x bits for the largest x such that 2^x < n.
# Any extra characters can wrap around to emit repeated binary values. We can randomly use those as to throw off any frequency analysis

# a map from a unicode character to a set of all characters that it is homoglyphic with
homoglyphs = {}

# a map from a unicode character to the binary that it represents
char_to_bin = {}

def populate_lookups(glyphs):
    for homoglyph_list in glyphs:
        # set each glyph as homoglyphic with all others
        for glyph in homoglyph_list:
            homoglyphs[glyph] = set()
            for o_glyph in homoglyph_list:
                if o_glyph is not glyph:
                    homoglyphs[glyph].add(o_glyph)

        # wrap characters and assign binary values
        max_binary_value = 2 ** math.floor(math.log2(len(homoglyph_list)))

        for i in range(len(homoglyph_list)):
            # wrap value
            mod_val = i % max_binary_value
            # assign the ith character in the homoglyphs list to a binary value
            char_to_bin[homoglyph_list[i]] = bin(mod_val)

#TODO use frequency analysis to estimate bits per character for the given font

out = get_duplicate_glyphs("Fonts/Arial-Unicode.ttf")
write_homoglyphs(out, "arial.hgy")
