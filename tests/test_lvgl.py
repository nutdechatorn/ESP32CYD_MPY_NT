"""
test_lvgl.py - a small interactive LVGL widget demo.

A button, a slider and a label; the button and slider react to touch.
Confirms LVGL rendering + input working together.

Run:  ./run.sh test_lvgl.py
"""

import lvgl as lv
import lcd_bus
import time
import board

board.backlight(100)
board.calibrate_touch()

W, H = board.size()
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x101018), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

title = lv.label(scr)
title.set_text('CYD LVGL demo')
title.align(lv.ALIGN.TOP_MID, 0, 8)

clicks = 0
count_label = lv.label(scr)
count_label.set_text('taps: 0')
count_label.align(lv.ALIGN.TOP_MID, 0, 40)


def on_button(e):
    global clicks
    if e.get_code() == lv.EVENT.CLICKED:
        clicks += 1
        count_label.set_text('taps: %d' % clicks)
        print('button clicked', clicks)


btn = lv.button(scr)
btn.set_size(160, 60)
btn.align(lv.ALIGN.CENTER, 0, -40)
btn.add_event_cb(on_button, lv.EVENT.ALL, None)
btn_label = lv.label(btn)
btn_label.set_text('CLICK ME')
btn_label.center()

value_label = lv.label(scr)
value_label.align(lv.ALIGN.CENTER, 0, 40)
value_label.set_text('value: 50')


def on_slider(e):
    if e.get_code() == lv.EVENT.VALUE_CHANGED:
        value_label.set_text('value: %d' % slider.get_value())


slider = lv.slider(scr)
slider.set_size(220, 20)
slider.set_range(0, 100)
slider.set_value(50, 0)
slider.align(lv.ALIGN.CENTER, 0, 70)
slider.add_event_cb(on_slider, lv.EVENT.ALL, None)

scr.invalidate()
print('try tapping the button and dragging the slider')

# Keep the script (and serial connection) alive so the LVGL loop runs.
while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
