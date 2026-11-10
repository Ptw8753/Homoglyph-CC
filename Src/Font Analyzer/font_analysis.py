import math

from Src.Common.homoglyph_file_utils import read_homoglyphs, write_homoglyphs
from duplicate_glyph_finder import get_duplicate_glyphs
from frequency_analyisis import read_frequency_from_frq


# takes the current list of homoglyphs as well as a .frq frequency file to determine a bitrate (bits-per-char) of the font
def font_frequency_analysis(hgy_filepath: str, frq_filepath: str):
    homoglyphs, _ = read_homoglyphs(hgy_filepath)

    bits_per_char = 0

    char_total, frequencies = read_frequency_from_frq(frq_filepath)
    # for each char, add it's frequency times the # bits it can encode
    for char in frequencies:
        if char in homoglyphs:
            bits_per_char += (frequencies[char] / char_total) * math.floor(math.log2(len(homoglyphs[char])+1))

    print(f"{bits_per_char} bits per char")

# run the glyph matcher
homoglyphs = get_duplicate_glyphs("Fonts/ttf/Arial-Unicode.ttf")

# write the font to a .hgy file
write_homoglyphs(homoglyphs, "Fonts/hgy/arial.hgy")

# analyze the frequency for the font
font_frequency_analysis("Fonts/hgy/comic-sans.hgy", "Frequency Analysis/tale_of_two_cities.frq")