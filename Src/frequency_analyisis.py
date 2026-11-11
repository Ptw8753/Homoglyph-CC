import math

from Common.homoglyph_file_utils import read_homoglyphs


# takes the current list of homoglyphs as well as a .frq frequency file to determine a bitrate (bits-per-char) of the font
# returns the bits per char
def font_frequency_analysis(hgy_filepath: str, frq_filepath: str):
    homoglyphs, _ = read_homoglyphs(hgy_filepath)

    bits_per_char = 0

    char_total, frequencies = read_frequency_from_frq(frq_filepath)
    # for each char, add it's frequency times the # bits it can encode
    for char in frequencies:
        if char in homoglyphs:
            bits_per_char += (frequencies[char] / char_total) * math.floor(math.log2(len(homoglyphs[char])+1))

    return bits_per_char

def write_frequency_to_frq(char_total: int, frequencies: dict[str, int], filepath: str) -> None:
    lines = [str(char_total) + "\n"]

    for char in frequencies.keys():
        lines.append(char + str(frequencies[char]) + "\n")

    with open(filepath, "w", encoding='utf_8') as file:
        file.writelines(lines)

def read_frequency_from_plaintext(filepath: str) -> tuple[int, dict[str, int]]:
    char_total = 0
    char_frequencies = {}

    with open(filepath, "r", encoding='utf_8') as file:
        # for every char on every line
        for line in file.readlines():
            for char in line:
                # skip the newline char
                if char != "\n":
                    # init in the table if we haven't seen this one yet
                    if char not in char_frequencies:
                        char_frequencies[char] = 0
                    # add 1 to the frequency
                    char_frequencies[char] += 1
                    char_total += 1

    return char_total, char_frequencies

def read_frequency_from_frq(filepath: str) -> tuple[int, dict[str, int]]:

    char_frequencies = {}

    with open(filepath, "r", encoding='utf_8') as file:
        char_total = int(file.readline().strip())
        # for every char on every line
        for line in file.readlines():
            char_frequencies[line[0]] = int(line.strip()[1:])

    return char_total, char_frequencies

def analyze_frequency(char_total: int, frequencies: dict[str, int]):
    arr = []
    for key in frequencies.keys():
        arr.append((key, frequencies[key] / char_total))
    arr = sorted(arr, key=lambda x: x[1], reverse=True)
    for item in arr:
        print(f"{item[0]}: {item[1] * 100} %")

