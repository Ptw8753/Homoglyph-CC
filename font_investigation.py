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
def find_duplicate_glyphs(font):
    hashes = {}

    for glyph_name in font.getGlyphOrder():
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


def get_unicode_map(font):
    """
    Map glyph name -> list of Unicode code points.
    """
    unicode_map = {}

    for table in font["cmap"].tables:
        if not table.isUnicode():
            continue

        for codepoint, glyph_name in table.cmap.items():
            if glyph_name not in unicode_map:
                unicode_map[glyph_name] = []
            unicode_map[glyph_name].append(codepoint)

    return unicode_map


font = TTFont("Arial-Unicode.ttf")

duplicates = find_duplicate_glyphs(font)
unicode_map = get_unicode_map(font)

for glyphs in duplicates:
    values = []

    for glyph_name in glyphs:
        for cp in unicode_map.get(glyph_name, []):
            values.append(f"U+{cp:04X} ({chr(cp)})")

    print(", ".join(sorted(values)))
