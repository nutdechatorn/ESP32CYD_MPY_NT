"""
boot_check.py - quickest smoke test.

Imports the hardware, prints a board/firmware report, flashes the screen
white then grey, and gives a short backlight pulse. No touch needed.

Run:  mpremote run tests/boot_check.py
"""

import time
import lvgl as lv
import board

board.dump_info()

scr = lv.screen_active()
for color in (0xFFFFFF, 0x808080, 0x000000):
    scr.set_style_bg_color(lv.color_hex(color), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    scr.invalidate()
    time.sleep(0.4)

for level in (0, 40, 80, 100):
    board.backlight(level)
    time.sleep(0.2)

board.backlight(100)
print('boot_check OK')
