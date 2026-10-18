"""
test_thai_sizes.py - render the same shaped Thai line at several font sizes
so the smallest legible size can be picked on the panel.

Each row: a gray size tag, the shaped text (white) and an unshaped lv.label
reference (dark gray). Same font file, only the pixel size changes.

Run:  ./run.sh test_thai_sizes.py
Edit `sizes` below to test other pixel sizes.
"""

import lvgl as lv
import lcd_bus
import time
import board
import fs_driver
import thai

board.backlight(100)
W, H = board.size()
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

drv = lv.fs_drv_t()
fs_driver.fs_register(drv, "A")

sizes = [24, 22, 20, 18, 16, 14]

LINE = "\u0e14\u0e35\u0e49 \u0e1b\u0e35\u0e49 \u0e19\u0e49\u0e33 \u0e1d\u0e49\u0e32\u0e22 \u0e0d\u0e32\u0e15\u0e34"

y = 4
for sz in sizes:
    try:
        tf = thai.ThaiFont("A:/Sarabun-Regular.ttf", sz, 64)
    except Exception as e:  # noqa: BLE001
        print("size", sz, "FAILED:", e)
        y += sz + 6
        continue

    items, w = tf.shape(LINE)
    marks = [(c, p, r) for (c, p, r, m) in items if m]
    print("size", sz, "line_height", tf.line_height, "base_line", tf.base_line,
          "w", w, "marks", marks)

    tag = lv.label(scr)
    tag.set_text(str(sz))
    tag.set_style_text_color(lv.color_hex(0x404040), 0)
    tag.set_pos(2, y)

    ref = lv.label(scr)  # unshaped reference
    ref.set_text(LINE)
    ref.set_style_text_font(tf.font, 0)
    ref.set_style_text_color(lv.color_hex(0x585858), 0)
    ref.set_pos(160, y)

    thai.render(scr, tf, LINE, 22, y, lv.color_hex(0xFFFFFF))

    y += tf.line_height + 6

scr.invalidate()
print("done")

while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
