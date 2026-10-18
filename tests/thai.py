"""
thai.py - minimal Thai text shaper + renderer for LVGL MicroPython.

LVGL has no OpenType shaping (no HarfBuzz/GPOS), so combining marks that the
font positions via GPOS (e.g. a tone mark stacked above an upper vowel) are
drawn with their *default* offsets and collide.

This module implements just enough of the Thai shaping model to fix that:

  * split text into clusters (leading vowel + consonant + marks + trailing),
  * stack upper marks (upper vowel -> tone -> other upper marks) so they never
    overlap, measuring real glyph metrics from the font
    (`font.get_glyph_dsc` -> adv_w / box_w / box_h / ofs_x / ofs_y),
  * draw with LVGL.

Rendering uses LVGL's own label widget for the bulk of the text (one label per
run of "base width" glyphs) and a separate, vertically shifted label for each
upper mark that had to be raised. All labels share one baseline, so LVGL's
per-glyph ofs_x/ofs_y handling stays correct - only the raise is ours.

Geometry (from lib/lvgl/src/draw/lv_draw_label.c):
    glyph_left = pos.x + ofs_x
    glyph_top  = pos.y + line_height - base_line - box_h - ofs_y
so `ofs_y` is the distance from the baseline up to the glyph's *bottom* edge.
A mark is "raised" by moving its label up by `raise` pixels.

Kerning is disabled when the font is created so that our pen advances match
LVGL's layout exactly.
"""

import lvgl as lv

# --- Thai code point classes ------------------------------------------------

_LEAD = frozenset(map(ord, "\u0e40\u0e41\u0e42\u0e43\u0e44"))          # เ แ โ ใ ไ
_TRAIL = frozenset(map(ord, "\u0e30\u0e32\u0e33\u0e45\u0e46"))         # ะ า ำ ๅ ๆ
_UVOWEL = frozenset(map(ord, "\u0e31\u0e34\u0e35\u0e36\u0e37"))        # ั ิ ี ึ ื
_UMARK = frozenset(map(ord, "\u0e47\u0e4c\u0e4d\u0e4e"))               # ็ ์ ํ ๎
_TONE = frozenset(map(ord, "\u0e48\u0e49\u0e4a\u0e4b"))                # ่ ้ ๊ ๋
_LOWER = frozenset(map(ord, "\u0e38\u0e39\u0e3a"))                     # ุ ู ฺ

# stacking priority for upper marks: lower (closer to base) first
_PRIO = {"V": 0, "O": 1, "M": 2}


def _is_base(o):
    # consonants ก..ฮ (incl. ฤ ฦ ฃ ฅ), paiyannoi ฯ, baht ฿, Thai digits
    return (0x0E01 <= o <= 0x0E2F) or o == 0x0E3F or (0x0E50 <= o <= 0x0E59)


def _kind(o):
    if o in _LEAD:
        return "L"
    if o in _TRAIL:
        return "T"
    if o in _UVOWEL:
        return "V"
    if o in _UMARK:
        return "M"
    if o in _TONE:
        return "O"
    if o in _LOWER:
        return "D"
    if _is_base(o):
        return "C"
    return "X"


class ThaiFont:
    """A TinyTTF font plus the metrics/shaping helpers used by the renderer."""

    def __init__(self, path, size, cache_size=256):
        self.font = lv.tiny_ttf_create_file_ex(
            path, size, lv.FONT_KERNING.NONE, cache_size
        )
        self.size = size
        self.line_height = self.font.line_height
        self.base_line = self.font.base_line

    def _dsc(self, ch):
        gd = lv.font_glyph_dsc_t()
        lv.font_t.get_glyph_dsc(self.font, gd, ord(ch), 0)
        return gd

    def adv(self, ch):
        return self._dsc(ch).adv_w

    def top(self, ch):
        """Distance of the glyph's top above the baseline (px)."""
        gd = self._dsc(ch)
        return gd.ofs_y + gd.box_h

    def shape(self, text):
        """
        Return (items, width) where items is a list of
        [char, pen_x, raise_y, is_mark]; pen_x is the x offset from the start
        of the text, raise_y is how far the glyph must be lifted (px).
        """
        items = []
        pen = 0
        i = 0
        n = len(text)
        while i < n:
            k = _kind(ord(text[i]))
            if k not in ("C", "L"):
                ch = text[i]
                items.append([ch, pen, 0, False])
                pen += self.adv(ch)
                i += 1
                continue

            # leading vowels (preposed) then the base
            while i < n and _kind(ord(text[i])) == "L":
                ch = text[i]
                items.append([ch, pen, 0, False])
                pen += self.adv(ch)
                i += 1

            base = None
            if i < n and _kind(ord(text[i])) == "C":
                base = text[i]
                items.append([base, pen, 0, False])
                pen += self.adv(base)
                i += 1

            cpen = pen  # pen after the base: where marks attach
            floor = self.top(base) if base else 0

            marks = []
            while i < n:
                kk = _kind(ord(text[i]))
                if kk in ("V", "M", "O", "D"):
                    marks.append((text[i], kk))
                    i += 1
                elif kk == "T":
                    ch = text[i]
                    items.append([ch, pen, 0, False])
                    t = self.top(ch)
                    if t > floor:
                        floor = t
                    pen += self.adv(ch)
                    i += 1
                else:
                    break

            # upper marks: stable-sort by stack priority, then place each one
            # above everything already placed so they cannot overlap.
            upper = sorted(
                (m for m in marks if m[1] in _PRIO), key=lambda m: _PRIO[m[1]]
            )
            for ch, _kk in upper:
                gd = self._dsc(ch)
                nb = gd.ofs_y
                tb = nb if nb > floor else floor
                items.append([ch, cpen, tb - nb, True])
                floor = tb + gd.box_h

            # lower marks sit below the base: natural position is fine.
            for ch, kk in marks:
                if kk == "D":
                    items.append([ch, cpen, 0, True])

        return items, pen


def render(parent, thai_font, text, x, y, color, font=None):
    """
    Draw `text` into `parent` with its baseline top at (x, y).

    `y` is the top of the line (the same reference a normal lv.label uses).
    `color` is an lv_color_t. Returns the list of created label objects.
    """
    f = font or thai_font.font
    items, _w = thai_font.shape(text)

    # group consecutive base-width glyphs into single labels
    runs = []
    cur = None  # [pen, chars]
    for ch, pen, raise_y, is_mark in items:
        if is_mark:
            if cur is not None:
                runs.append((cur[1], cur[0], 0))
                cur = None
            runs.append((ch, pen, raise_y))
        else:
            if cur is None:
                cur = [pen, ch]
            else:
                cur[1] += ch
    if cur is not None:
        runs.append((cur[1], cur[0], 0))

    objs = []
    for chars, pen, raise_y in runs:
        lbl = lv.label(parent)
        lbl.set_text(chars)
        lbl.set_style_text_font(f, 0)
        lbl.set_style_text_color(color, 0)
        lbl.set_style_pad_all(0, 0)
        lbl.set_style_bg_opa(0, 0)
        lbl.set_style_border_width(0, 0)
        lbl.add_flag(lv.obj.FLAG.OVERFLOW_VISIBLE)
        lbl.set_pos(x + pen, y - raise_y)
        objs.append(lbl)
    return objs


def text_width(thai_font, text):
    _items, w = thai_font.shape(text)
    return w
