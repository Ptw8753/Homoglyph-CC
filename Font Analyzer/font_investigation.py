from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import hashlib

# Record the glyph being drawn, then return the hash of the steps
def glyph_hash(font, glyph_name):
    glyph_set = font.getGlyphSet()
    glyph = glyph_set[glyph_name]

    pen = RecordingPen()
    glyph.draw(pen)

    return hashlib.sha256(
        repr(pen.value).encode("utf-8")
    ).hexdigest()

# returns a list of lists [duplicates]
def find_duplicate_glyphs(font, unicode_map):
    hashes = {}

    for glyph_name in font.getGlyphOrder() and unicode_map:
        # get the hash of the glyph
        h = glyph_hash(font, glyph_name)
        # add it to the list of all hashes
        if h not in hashes:
            hashes[h] = []
        hashes[h].append(glyph_name)

    return [
        glyphs for glyphs in hashes.values()
        if len(glyphs) > 1
    ]


# get a map of all glyph names to their unicode values
def get_unicode_map(font):
    unicode_map = {}

    for table in font["cmap"].tables:
        if not table.isUnicode():
            continue

        for codepoint, glyph_name in table.cmap.items():
            if glyph_name not in unicode_map:
                unicode_map[glyph_name] = []
            unicode_map[glyph_name].append(codepoint)

    return unicode_map

# returns a list of lists of unicode values
# this is a sorted list for all characters that render identically
def get_duplicate_glyphs(font_filepath):
    # load the font
    font = TTFont(font_filepath)

    unicode_map = get_unicode_map(font)

    # find duplicates
    duplicates = find_duplicate_glyphs(font, unicode_map)

    # # Print all duplicate glyphs
    # for glyphs in duplicates:
    #     values = []
    #
    #     for glyph_name in glyphs:
    #         for cp in unicode_map[glyph_name]:
    #             values.append(f"U+{cp:04X} ({chr(cp)})")
    #
    #     if len(values) > 1:
    #         print(", ".join(sorted(values)))

    ret_values = []
    for glyphs in duplicates:
        values = []

        for glyph_name in glyphs:
            for cp in unicode_map[glyph_name]:
                values.append(chr(cp))

        if len(values) > 1:
            ret_values.append(values)

    return ret_values