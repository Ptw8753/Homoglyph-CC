
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

# reads a given text file in and returns a .frq file with frequency stats for frequency
def count_frequency(filepath_in: str, filepath_out: str):
    char_total, frequencies = read_frequency_from_plaintext(filepath_in)
    analyze_frequency(char_total, frequencies)
    write_frequency_to_frq(char_total, frequencies, filepath_out)

#char_total, frequencies = read_frequency_from_frq("../../Frequency Analysis/tale_of_two_cities.frq")
#analyze_frequency(char_total, frequencies)
#count_frequency("../Frequency Analysis/tale_of_two_cities.txt", "../Frequency Analysis/tale_of_two_cities.frq")
