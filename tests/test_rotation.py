"""
test_rotation.py - cycle all four rotations so mirroring can be spotted.

For each rotation the script draws:
  * top border RED, bottom GREEN, left YELLOW, right BLUE  -> a mirror swaps these
  * corner labels TL / TR / BL / BR                        -> a mirror swaps corners
  * a big centered "ROT n" label                           -> text shows mirroring

The classic CYD panel is BGR and portrait-native (240x320), driven as landscape
via rotation _90. With `_ORIENTATION_TABLE = [64, 32, 128, 224]` all four
rotations are upright: red on top, green on bottom, yellow on left, blue on
right, and the corner labels match their corners.

Run:  ./run.sh test_rotation.py     (or: mpremote run tests/test_rotation.py)
"""

import lvgl as lv
import board
import lcd_bus
import time

# End on _180 so the final frame (which stays after the script exits) is the
# one most likely under investigation.
rots = [
    (lv.DISPLAY_ROTATION._0, '0'),
    (lv.DISPLAY_ROTATION._90, '90'),
    (lv.DISPLAY_ROTATION._270, '270'),
    (lv.DISPLAY_ROTATION._180, '180'),
]


def bar(scr, x, y, w, h, color):
    o = lv.obj(scr)
    o.set_pos(x, y)
    o.set_size(w, h)
    o.set_style_bg_color(lv.color_hex(color), 0)
    o.set_style_bg_opa(lv.OPA.COVER, 0)
    o.set_style_radius(0, 0)
    o.set_style_border_width(0, 0)
    o.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    return o


def txt(scr, s, x, y):
    l = lv.label(scr)
    l.set_text(s)
    l.set_pos(x, y)
    l.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    l.set_style_text_font(lv.font_montserrat_16, 0)
    return l


for rot, name in rots:
    board.lcd.set_rotation(rot)
    W, H = board.size()
    scr = lv.screen_active()
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)

    b = 8
    bar(scr, 0, 0, W, b, 0xFF0000)          # top red
    bar(scr, 0, H - b, W, b, 0x00FF00)      # bottom green
    bar(scr, 0, 0, b, H, 0xFFFF00)          # left yellow
    bar(scr, W - b, 0, b, H, 0x0000FF)      # right blue

    txt(scr, 'TL', 16, 16)
    txt(scr, 'TR', W - 60, 16)
    txt(scr, 'BL', 16, H - 46)
    txt(scr, 'BR', W - 60, H - 46)

    lbl = lv.label(scr)
    lbl.set_text('ROT ' + name)
    lbl.set_style_text_font(lv.font_montserrat_16, 0)
    lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    lbl.set_width(W)
    lbl.set_height(30)
    lbl.set_pos(0, H // 2 - 15)
    lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)

    scr.invalidate()

    # ~5s per rotation
    for _ in range(50):
        lcd_bus._pump_main_thread()
        time.sleep_ms(100)

print('done cycling rotations')
