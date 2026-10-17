"""
test_backlight.py - fade the backlight (pin 21, PWM) up and down.

Useful to confirm the PWM backlight control and that you can dim the
panel. Stops after a few cycles.

Run:  mpremote run tests/test_backlight.py
"""

import time
import lvgl as lv
import board

W, H = board.size()
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x202020), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

label = lv.label(scr)
label.set_text('BACKLIGHT')
label.center()
scr.invalidate()

print('fading 0 <-> 100')
for cycle in range(3):
    for level in range(0, 101, 4):
        board.backlight(level)
        time.sleep(0.02)
    for level in range(100, -1, -4):
        board.backlight(level)
        time.sleep(0.02)

board.backlight(100)
print('done - backlight at 100%')
