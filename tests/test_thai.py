"""
test_thai.py - render shaped Thai text and compare with the unshaped original.

Left column  : shaped with thai.render()  (marks stacked, no collision)
Right column : plain lv.label with the same font (marks collide) - reference

Run:  ./run.sh test_thai.py
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

tf = thai.ThaiFont("A:/Sarabun-Regular.ttf", 14, 256)
print("line_height", tf.line_height, "base_line", tf.base_line)

TESTS = ["ดี้", "ดี", "เด็ด", "กำ", "ภาษาไทย", "ปี้", "ฝ้าย", "น้ำ", "ญาติ", "f(x)=2"]

y = 8
for t in TESTS:
    items, w = tf.shape(t)
    summary = [(c, p, r) for (c, p, r, m) in items if m]
    print(repr(t), "w=%d" % w, "marks(px,raise)=", summary)

    ref = lv.label(scr)  # unshaped reference
    ref.set_text(t)
    ref.set_style_text_font(tf.font, 0)
    ref.set_style_text_color(lv.color_hex(0x808080), 0)
    ref.set_pos(200, y)

    thai.render(scr, tf, t, 10, y, lv.color_hex(0xFFFFFF))

    y += tf.line_height + 4

scr.invalidate()
print("done")

while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
