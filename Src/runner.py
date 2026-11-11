from Common.homoglyph_file_utils import write_homoglyphs
from Src.duplicate_glyph_finder import get_duplicate_glyphs
from Src.frequency_analyisis import font_frequency_analysis, write_frequency_to_frq, read_frequency_from_plaintext
from Src.encode import encode
from Src.decode import decode

# this serves as a single spot for running stuff, just to make stuff a little easier
# comment out or change lines that you don't want :)

### IDENTICAL GLYPH DETECTION
font_ttf = "Fonts/ttf/Arial-Unicode.ttf"
font_hgy = "Fonts/hgy/arial.hgy"

print(f"1. Analyzing font at {font_hgy}")

# 1. Analyze a truetype font (ttf) for homoglyphs
homoglyphs = get_duplicate_glyphs(font_ttf)

# 2. Write the font to a .hgy file
write_homoglyphs(homoglyphs, font_hgy)

### FREQUENCY ANALYSIS
frequency_analysis_txt = "Frequency Analysis/tale_of_two_cities.txt"
frequency_analysis_frq = "Frequency Analysis/tale_of_two_cities.frq"

print("2. Performing frequency analysis on the font")

# 1. Count chars
char_total, frequencies = read_frequency_from_plaintext(frequency_analysis_txt)
# 2. Write to a frq file
write_frequency_to_frq(char_total, frequencies, frequency_analysis_frq)
# 3. Analyze the frequency on the given font
bits_per_char = font_frequency_analysis(font_hgy, frequency_analysis_frq)
print(f"\tThe analyzed font can encode at {bits_per_char} bits per char")

### ENCODE / DECODE
plaintext_txt = "plaintext.txt"
modified_txt = "modified.txt"
secret_message = "This is my secret message!"

print(f"3. Encoding \"{secret_message}\" within the text at {plaintext_txt} and writing the result to {modified_txt}")

# encode the message
encode(plaintext_txt, modified_txt, font_hgy, secret_message)

print(f"4. Decoding from {modified_txt}")

# decode the message
decoded_secret = decode(modified_txt, font_hgy)

print(f"\tThe decoded secret is \"{decoded_secret}\"")