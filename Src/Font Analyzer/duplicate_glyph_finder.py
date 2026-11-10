from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
import hashlib


def glyph_hash(font, glyph_name):
    glyph_set = font.getGlyphSet()

    # Decompose composite glyphs into their actual outlines
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(pen)

    # Normalize the drawing commands into a hashable representation
    return hashlib.sha256(
        repr(pen.value).encode("utf-8")
    ).hexdigest()


def get_unicode_map(font):
    unicode_map = {}

    for table in font["cmap"].tables:
        if not table.isUnicode():
            continue

        for codepoint, glyph_name in table.cmap.items():
            unicode_map.setdefault(glyph_name, []).append(codepoint)

    return unicode_map


def get_duplicate_glyphs(font_filepath):
    font = TTFont(font_filepath)
    unicode_map = get_unicode_map(font)

    # hash -> all Unicode characters producing that outline
    hashes = {}

    for glyph_name, codepoints in unicode_map.items():
        h = glyph_hash(font, glyph_name)

        for cp in codepoints:
            hashes.setdefault(h, []).append(cp)

    # Return groups of characters with identical outlines
    return [
        [chr(cp) for cp in sorted(codepoints)]
        for codepoints in hashes.values()
        if len(codepoints) > 1
    ]
