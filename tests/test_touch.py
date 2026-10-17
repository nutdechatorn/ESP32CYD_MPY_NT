"""
test_touch.py - calibrate and read the XPT2046 touch panel.

1. Runs the interactive on-screen calibration if it has not been done
   (tap the red square at the four corners and the centre in turn).
2. Then draws a green dot that follows your finger and prints "x,y" to
   the serial console.

Run:  ./run.sh test_touch.py
"""

import lvgl as lv
import lcd_bus
import time
import board

board.backlight(100)

print('calibrating (tap the red square at the 4 corners + centre)...')
board.calibrate_touch()
print('calibration stored')

W, H = board.size()
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

label = lv.label(scr)
label.set_pos(8, 8)
label.set_text('touch the screen')

dot = lv.obj(scr)
dot.set_size(24, 24)
dot.set_style_bg_color(lv.color_hex(0x00FF00), 0)
dot.set_style_bg_opa(lv.OPA.COVER, 0)
dot.set_style_radius(lv.RADIUS_CIRCLE, 0)
dot.set_style_border_width(0, 0)
dot.add_flag(lv.obj.FLAG.HIDDEN)


def on_event(e):
    code = e.get_code()
    if code == lv.EVENT.PRESSING:
        # `lv.indev_active()` returns None here; read the point from the
        # pointer driver instead.
        pt = lv.point_t()
        board.touch.get_point(pt)
        label.set_text('%d , %d' % (pt.x, pt.y))
        print('touch', pt.x, pt.y)
        dot.set_pos(pt.x - 12, pt.y - 12)
        dot.remove_flag(lv.obj.FLAG.HIDDEN)
    elif code == lv.EVENT.RELEASED:
        dot.add_flag(lv.obj.FLAG.HIDDEN)


# A transparent full-screen catcher for touch events.
area = lv.obj(scr)
area.set_size(W, H)
area.set_pos(0, 0)
area.set_style_bg_opa(lv.OPA.TRANSP, 0)
area.set_style_border_width(0, 0)
area.add_flag(lv.obj.FLAG.CLICKABLE)
area.add_event_cb(on_event, lv.EVENT.ALL, None)

scr.invalidate()
print('drag your finger on the panel')

# Keep the script (and the serial connection) alive so the LVGL loop runs;
# `mpremote run` exits as soon as the top-level code returns.
while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
