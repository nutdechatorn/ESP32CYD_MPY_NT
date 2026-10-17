"""
test_display.py - exercise the ILI9341 panel.

Shows full-screen colour fills then three vertical R/G/B bars.
Leave it running to watch the pattern; press Ctrl-C to stop.

Run:  mpremote run tests/test_display.py
"""

import time
import lvgl as lv
import board

board.backlight(100)
W, H = board.size()
print('panel %dx%d' % (W, H))


def fill(color):
    scr = lv.screen_active()
    scr.set_style_bg_color(lv.color_hex(color), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    scr.invalidate()


print('filling colours...')
for color in (0x000000, 0xFFFFFF, 0xFF0000, 0x00FF00, 0x0000FF):
    fill(color)
    time.sleep(0.6)

# Three vertical bars.
print('R/G/B bars...')
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
bars = (0xFF0000, 0x00FF00, 0x0000FF)
bar_w = W // len(bars)
for i, color in enumerate(bars):
    bar = lv.obj(scr)
    bar.set_pos(i * bar_w, 0)
    bar.set_size(bar_w, H)
    bar.set_style_bg_color(lv.color_hex(color), 0)
    bar.set_style_bg_opa(lv.OPA.COVER, 0)
    bar.set_style_radius(0, 0)
    bar.set_style_border_width(0, 0)
    bar.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

scr.invalidate()
print('done - bars on screen')
