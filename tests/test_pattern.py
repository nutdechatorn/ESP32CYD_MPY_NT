"""
test_pattern.py - visual bounds / orientation check for the CYD panel.

Draws a full-screen border, four distinct corner blocks, a centre crosshair
and labels, so you can confirm that:

  * the image covers the WHOLE panel (no black band on any edge),
  * it is upright (labels read normally, not rotated/mirrored),
  * the colours are correct (corner blocks: TL white, TR red, BL green, BR blue).

Run:  mpremote run tests/test_pattern.py
"""

import lvgl as lv
import board

board.backlight(100)
W, H = board.size()
print('panel %dx%d' % (W, H))

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)


def block(x, y, w, h, color):
    o = lv.obj(scr)
    o.set_pos(x, y)
    o.set_size(w, h)
    o.set_style_bg_color(lv.color_hex(color), 0)
    o.set_style_bg_opa(lv.OPA.COVER, 0)
    o.set_style_radius(0, 0)
    o.set_style_border_width(0, 0)
    o.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    return o


b = 4  # border thickness

block(0, 0, W, b, 0xFFFFFF)          # top border
block(0, H - b, W, b, 0xFFFFFF)      # bottom border
block(0, 0, b, H, 0xFFFFFF)          # left border
block(W - b, 0, b, H, 0xFFFFFF)      # right border

c = 28  # corner block size
block(b, b, c, c, 0xFFFFFF)                  # top-left   white
block(W - b - c, b, c, c, 0xFF0000)          # top-right  red
block(b, H - b - c, c, c, 0x00FF00)          # bottom-left green
block(W - b - c, H - b - c, c, c, 0x0000FF)  # bottom-right blue

cx, cy = W // 2, H // 2
block(cx - 1, 0, 2, H, 0xFFFF00)     # vertical crosshair (yellow)
block(0, cy - 1, W, 2, 0xFFFF00)     # horizontal crosshair (yellow)

top = lv.label(scr)
top.set_text('TOP')
top.align(lv.ALIGN.TOP_MID, 0, 8)

mid = lv.label(scr)
mid.set_text('%d x %d' % (W, H))
mid.align(lv.ALIGN.CENTER, 0, 0)

scr.invalidate()
print('pattern drawn - check full coverage + orientation + colours')
