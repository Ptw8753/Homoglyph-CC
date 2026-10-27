# Homoglyph Covert Channel Detector
# Detects potential hidden messages using homoglyph substitutions.
#
# TODO:
# - Improve detection accuracy
# - Implement message header detection
# - Reduce false positives
# - Determine message boundaries

import argparse
from Common.homoglyph_file_utils import read_homoglyphs


# Read existing homoglyph mappings
homoglyphs, char_to_bin = read_homoglyphs("arial.hgy")


def extract_bits(text):
    """
    Extract binary values from characters using
    the existing homoglyph mapping.
    """

    bits = ""

    for char in text:
        if char in char_to_bin:
            bits += char_to_bin[char]

    return bits


def decode_bits(bits):
    """
    Convert extracted bits into 7-bit ASCII.
    """

    message = ""

    for i in range(0, len(bits) - 6, 7):
        binary = bits[i:i + 7]

        character = chr(int(binary, 2))
        message += character

    return message


def analyze_text(text):
    """
    Analyze text for characters that have
    homoglyph mappings.
    """

    total_chars = len(text)
    mapped_chars = 0
    suspicious_chars = []

    for index, char in enumerate(text):

        if char in char_to_bin:
            mapped_chars += 1

            suspicious_chars.append({
                "position": index,
                "character": char,
                "binary": char_to_bin[char]
            })

    if total_chars > 0:
        percentage = (mapped_chars / total_chars) * 100
    else:
        percentage = 0

    return mapped_chars, percentage, suspicious_chars


def compare_cover(original, encoded):
    """
    Compare the original cover text against
    the encoded text.

    Identify characters that were replaced
    with homoglyphs.
    """

    substitutions = []

    for index, (original_char, encoded_char) in enumerate(
        zip(original, encoded)
    ):

        if original_char != encoded_char:

            if original_char in homoglyphs:

                if encoded_char in homoglyphs[original_char]:

                    substitutions.append({
                        "position": index,
                        "original": original_char,
                        "encoded": encoded_char
                    })

    return substitutions


def detect(filepath="out.txt", cover_filepath=None):
    """
    Detect potential homoglyph covert channels.
    """

    with open(filepath, "r", encoding="utf-8") as file:
        text = file.read()

    print("\n===== Homoglyph Covert Channel Detector =====")

    print(f"\nAnalyzing file: {filepath}")

    # Analyze homoglyph characters
    mapped_chars, percentage, suspicious = analyze_text(text)

    print("\n--- Character Analysis ---")

    print(f"Total characters: {len(text)}")
    print(f"Characters with homoglyph mappings: {mapped_chars}")
    print(f"Mapped character percentage: {percentage:.2f}%")

    # Extract binary data
    bits = extract_bits(text)

    print("\n--- Binary Extraction ---")

    print(f"Extracted bits: {len(bits)}")

    # Attempt decoding
    decoded_message = decode_bits(bits)

    print("\n--- Potential Hidden Message ---")

    print(repr(decoded_message))

    # Determine printable character ratio
    if decoded_message:

        printable = sum(
            1 for char in decoded_message
            if char.isprintable()
        )

        printable_ratio = (
            printable / len(decoded_message)
        ) * 100

    else:
        printable_ratio = 0

    print(f"\nPrintable character ratio: {printable_ratio:.2f}%")

    # Basic detection heuristic
    print("\n--- Detection Results ---")

    if mapped_chars == 0:

        print("No mapped homoglyph characters detected.")

    elif printable_ratio >= 80:

        print("Potential hidden message detected.")
        print("Extracted data contains mostly printable characters.")

    else:

        print("Homoglyph mappings detected.")
        print("Unable to confidently identify a hidden message.")

    # Optional cover text comparison
    if cover_filepath:

        with open(
            cover_filepath, "r", encoding="utf-8"
        ) as file:

            original_text = file.read()

        substitutions = compare_cover(
            original_text,
            text
        )

        print("\n--- Cover Text Comparison ---")

        print(f"Homoglyph substitutions found: {len(substitutions)}")

        for substitution in substitutions:

            print(
                f"Position {substitution['position']}: "
                f"'{substitution['original']}' -> "
                f"'{substitution['encoded']}'"
            )

        if substitutions:

            print("\nPotential homoglyph covert channel detected.")

        else:

            print("\nNo homoglyph substitutions detected.")

        if len(original_text) != len(text):
            print(
                "\nWarning: Original and encoded texts "
                "have different lengths."
            )

    print("\n===== Analysis Complete =====\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Detect homoglyph covert channels."
    )

    parser.add_argument(
        "file",
        nargs="?",
        default="out.txt",
        help="File to analyze (default: out.txt)"
    )

    parser.add_argument(
        "--cover",
        help="Optional original cover text for comparison"
    )

    args = parser.parse_args()

    detect(args.file, args.cover)