# ESP32 CYD — MicroPython + LVGL User Manual (English)

> ไทย: [`manual.th.md`](manual.th.md)

A complete guide to using the prebuilt **MicroPython + LVGL** firmware on the
classic **ESP32 Cheap Yellow Display (CYD) — board ESP32-2432S028R**.

The manual covers the board, flashing, the REPL, the display and touch APIs,
the LVGL graphics library, every commonly used function, and a worked example
for each. All API names were checked against the actual firmware sources
(`lvgl.pyi`, the frozen `display`/`indev` modules, and the `tests/` scripts).

---

## Table of contents

1. [What you have](#1-what-you-have)
2. [Board & pin reference](#2-board--pin-reference)
3. [Quick start](#3-quick-start)
4. [The frozen `display` module](#4-the-frozen-display-module)
5. [The `board` helper](#5-the-board-helper)
6. [Display API — `ili9341`](#6-display-api--ili9341)
7. [Touch API — `xpt2046`](#7-touch-api--xpt2046)
8. [LVGL fundamentals](#8-lvgl-fundamentals)
9. [LVGL widgets](#9-lvgl-widgets)
10. [Events](#10-events)
11. [Styles](#11-styles)
12. [System modules](#12-system-modules)
13. [Complete example programs](#13-complete-example-programs)
14. [Binding quirks & gotchas](#14-binding-quirks--gotchas)
15. [Troubleshooting](#15-troubleshooting)
16. [The test suite](#16-the-test-suite)
17. [Rebuilding the firmware](#17-rebuilding-the-firmware)

---

## 1. What you have

The firmware image `firmware/ESP32-CYD-2432S028R-lvgl-micropython.bin` is a
single merged image containing:

| Component | Version |
| --- | --- |
| MicroPython | 1.27.0 |
| LVGL | 9.4.0 |
| ESP-IDF | 5.5.1 |
| Board | ESP32-2432S028R (ESP32-WROOM-32, 4 MB flash, **no PSRAM**) |

After flashing you get a Python REPL on the serial port, with the graphics
library (`lvgl`), the display driver (`ili9341`), the touch driver (`xpt2046`)
and the panel/touch already initialised by the frozen `display` module.

The **application partition is almost full** (~3.9 KB free), so the image
cannot grow much without enabling `optimize_size` and rebuilding. MicroPython
scripts you write live on a small FAT filesystem, not in the app partition, so
that is fine.

---

## 2. Board & pin reference

| Function | Signal | GPIO |
| --- | --- | --- |
| Display (ILI9341, SPI host 1) | MOSI | 13 |
| | MISO | 12 |
| | SCK | 14 |
| | CS | 15 |
| | DC | 2 |
| | Backlight (PWM) | 21 |
| | Reset | not connected |
| Touch (XPT2046, SPI host 2) | MOSI | 32 |
| | MISO | 39 |
| | SCK | 25 |
| | CS | 33 |
| | IRQ | 36 |

- Display resolution: **240x320 portrait** native, driven as **320x240
  landscape** with rotation `_90`.
- Panel colour order: **BGR** (handled by the config; you do not set it in code).
- Control pins (e.g. the RGB LED, speaker) are not wired by this firmware.

---

## 3. Quick start

### 3.1 Flash the firmware

Install esptool, find your serial port, then flash the merged image at offset
`0x0`. `--erase-all` erases the whole flash (including the saved touch
calibration).

```bash
pip install esptool

# macOS / Linux  — example port /dev/cu.usbserial-0001
python -m esptool --chip esp32 -p /dev/cu.usbserial-0001 -b 460800 \
  --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m --erase-all \
  0x0 ESP32-CYD-2432S028R-lvgl-micropython.bin
```

Windows: replace the port with `-p COM5` (check Device Manager).

List ports on macOS with `ls /dev/cu.*`; the CYD shows up as
`/dev/cu.usbserial-*`, `/dev/cu.wchusbserial*` or `/dev/cu.SLAB_USBtoUART`.

### 3.2 Open the REPL

The REPL runs at **115200 baud**.

```bash
pip install mpremote

mpremote connect /dev/cu.usbserial-0001 repl     # interactive prompt (Ctrl-] to exit)
```

`mpremote` uses `connect <port>`; it does **not** accept `--port`.

### 3.3 Run your first script

Create `hello.py`:

```python
import lvgl as lv
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x003060), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

label = lv.label(scr)
label.set_text('Hello CYD!')
label.center()
scr.invalidate()
```

Run it:

```bash
mpremote connect /dev/cu.usbserial-0001 run hello.py
```

> **Important:** `mpremote run` returns as soon as the script's top-level code
> finishes. For anything that must keep responding (touch, LVGL animation),
> end the script with a loop — see [§8.9](#89-the-main-loop).

---

## 4. The frozen `display` module

`import display` brings up the whole board. The module was generated from the
build config `display_configs/CYD-2432S028R.toml`; the equivalent Python it runs
is:

```python
import machine, lcd_bus, ili9341, lvgl as lv, xpt2046, task_handler

spi_bus = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2_000_000, cs=33)

display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=24_000_000, dc=2, cs=15)

display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=240,
    display_height=320,
    backlight_pin=21,
    backlight_on_state=ili9341.STATE_PWM,
    color_byte_order=ili9341.BYTE_ORDER_BGR,   # CYD panel is BGR
    color_space=lv.COLOR_FORMAT.RGB565,
    rgb565_byte_swap=True,
)
display._ORIENTATION_TABLE = [0, 32, 192, 160]  # index 1 (_90) = MADCTL 0x20
display.set_power(True)
display.init(1)
display.set_rotation(lv.DISPLAY_ROTATION._90)   # landscape 320x240
display.set_backlight(100)

indev = xpt2046.XPT2046(device=indev_device)

task_handler.TaskHandler()                       # pumps LVGL timers + flush
```

After `import display` you have two useful objects:

| Name | Type | What it is |
| --- | --- | --- |
| `display.display` | `ili9341.ILI9341` | the display driver (an LVGL `display_t` wrapper) |
| `display.indev` | `xpt2046.XPT2046` | the touch driver (an LVGL `indev_t` wrapper) |

The display is set as the LVGL default display, and the `TaskHandler` starts an
LVGL tick/flush timer in the background.

> `import display` only works once per power cycle. A MicroPython soft reset
> does **not** release the ESP32 SPI host, so a second `import display` in the
> same power cycle fails with `TypeError: can't convert str to int` when the SPI
> bus is re-created. Do a **hard reset** (see [§16](#16-the-test-suite)) between
> runs.

---

## 5. The `board` helper

`tests/board.py` is a small convenience wrapper (your own scripts can copy the
same functions). Importing it also does `import display`.

```python
import board
```

| Function | Returns | Description |
| --- | --- | --- |
| `board.lcd` | `ili9341.ILI9341` | the display driver |
| `board.touch` | `xpt2046.XPT2046` | the touch driver |
| `board.width()` | int | display width (320, landscape) |
| `board.height()` | int | display height (240, landscape) |
| `board.size()` | `(w, h)` | width and height together |
| `board.backlight(level)` | – | set backlight brightness, `0`–`100` (%) |
| `board.calibrate_touch(force=False)` | bool | interactive 5-point touch calibration |
| `board.reset_touch_cal()` | – | erase the stored touch calibration |
| `board.dump_info()` | – | print a firmware/board report |

Example:

```python
import board
print(board.size())          # (320, 240)
board.backlight(50)          # dim to 50%
board.dump_info()
```

---

## 6. Display API — `ili9341`

The class is `ili9341.ILI9341` (subclass of the shared `DisplayDriver`).
Module constants:

| Constant | Value | Meaning |
| --- | --- | --- |
| `ili9341.STATE_HIGH` | 1 | pin active high |
| `ili9341.STATE_LOW` | 0 | pin active low |
| `ili9341.STATE_PWM` | -1 | PWM output (used for the backlight) |
| `ili9341.BYTE_ORDER_RGB` | 0x00 | RGB colour order (default) |
| `ili9341.BYTE_ORDER_BGR` | 0x08 | BGR colour order (this panel) |

### 6.1 Backlight

```python
lcd = board.lcd
lcd.set_backlight(100)     # 0..100 (%)
lcd.set_backlight(0)       # off
print(lcd.get_backlight()) # 100.0
```

### 6.2 Power / reset

```python
lcd.set_power(True)
print(lcd.get_power())
lcd.reset()                # only if a reset pin is wired (it is not on the CYD)
```

### 6.3 Resolution & rotation

```python
print(lcd.get_horizontal_resolution())  # 320
print(lcd.get_vertical_resolution())    # 240
print(lcd.get_rotation())               # lv.DISPLAY_ROTATION._90
lcd.set_rotation(lv.DISPLAY_ROTATION._0)    # back to portrait 240x320
lcd.set_rotation(lv.DISPLAY_ROTATION._90)   # landscape 320x240 (default)
```

Rotation values: `lv.DISPLAY_ROTATION._0`, `._90`, `._180`, `._270`.

### 6.4 Raw controller commands (advanced)

`set_params` / `get_params` talk directly to the ILI9341 controller. For
example, to re-assert the landscape + BGR MADCTL byte (`0x28`):

```python
lcd.set_params(0x36, bytearray([0x28]))   # 0x20 (MV) | 0x08 (BGR)
```

### 6.5 Colour format & inversion

```python
lcd.set_color_format(lv.COLOR_FORMAT.RGB565)
print(lcd.get_color_format())
lcd.set_color_inversion(False)  # flip if black/white are inverted
```

### 6.6 Other useful methods

| Method | Description |
| --- | --- |
| `set_physical_resolution(w, h)` | set the panel's physical resolution |
| `set_offset(x, y)` / `get_offset_x()` / `get_offset_y()` | drawing offset |
| `set_dpi(dpi)` / `get_dpi()` | density (affects widget sizes) |
| `is_double_buffered()` | whether two draw buffers are used |
| `get_screen_active()` / `get_layer_top()` / `get_layer_sys()` / `get_layer_bottom()` | LVGL screen/layer objects |
| `set_theme(theme)` / `get_theme()` | LVGL theme |
| `set_default()` | make this the default display |
| `add_event_cb(cb, filter, user_data)` | listener for display events |
| `init(type=None)` | (re)run the panel init sequence |
| `del lcd` | delete the instance (the only supported way — `lcd.delete()` raises) |

---

## 7. Touch API — `xpt2046`

The class is `xpt2046.XPT2046` (subclass of `PointerDriver`). It is an LVGL
pointer input device.

Class attributes you can tune before creating the instance:
`touch_threshold = 400`, `confidence = 5`, `margin = 50`.

### 7.1 Reading the touch position

The most reliable way to read the current point (works inside event callbacks
too) is `get_point` with an `lv.point_t`:

```python
pt = lv.point_t()
board.touch.get_point(pt)
print(pt.x, pt.y)
```

`touch.get_point(pt)` fills `pt.x` / `pt.y` with the **screen** coordinate.

### 7.2 Calibration

| Member | Description |
| --- | --- |
| `touch.is_calibrated` | `True` when a calibration is stored |
| `touch.calibrate()` | **not usable on this board** (see below) |
| `board.calibrate_touch(force=False)` | interactive 5-point calibration (use this) |
| `board.reset_touch_cal()` | erase the stored calibration |
| `touch._cal` | the `TouchCalData` object (advanced) |

`touch._cal` (`TouchCalData`) fields — a 3x3 affine stored in NVS:
`alphaX, betaX, deltaX, alphaY, betaY, deltaY, mirrorX, mirrorY`, with
`save()` and `reset()`.

Example — calibrate if needed, then read a point:

```python
import lvgl as lv
import board

board.calibrate_touch()          # shows red squares; tap each in turn
pt = lv.point_t()
board.touch.get_point(pt)
print('screen', pt.x, pt.y)
```

> **Why not `touch.calibrate()`?** The frozen calibration forces the display to
> rotation `_0` while sizing its targets from the *landscape* dimensions, so the
> targets land off-screen. `board.calibrate_touch()` runs in the real landscape
> rotation and fits the affine to the pre-rotation coordinate that LVGL expects
> (LVGL applies the display rotation to pointer points a second time). Result:
> accurate to roughly 6 px at all corners and the centre.

### 7.3 Other pointer methods

| Method | Description |
| --- | --- |
| `touch.enable(en)` | enable/disable the device |
| `touch.get_state()` | `lv.INDEV_STATE.PRESSED` / `.RELEASED` |
| `touch.get_width()` / `get_height()` | the area the device reports |
| `touch.get_rotation()` | current display rotation |
| `touch.get_point(pt)` | fill `pt` with the screen coordinate |
| `touch.get_vect(pt)` | fill `pt` with the movement vector |
| `touch.get_scroll_obj()` / `get_scroll_dir()` / `get_gesture_dir()` | gesture info |
| `touch.set_cursor(obj)` | set a cursor object that follows the pointer |
| `touch.reset_long_press()` | reset long-press state |
| `touch.read()` | force a read |
| `touch.search_obj(pt)` | hit-test an `lv.point_t` |
| `touch.add_event_cb(cb, filter, user_data)` | listen to indev events |
| `xpt2046.XPT2046.active()` | the active pointer driver, or `None` |

> Inside an LVGL event callback, `lv.indev_active()` can return `None` in this
> binding — read the point from the driver (`board.touch.get_point(pt)`) instead.

---

## 8. LVGL fundamentals

`import lvgl as lv`. The library is initialised by `import display`; if you
build your own, call `lv.init()`.

### 8.1 Screens

Every display has an "active screen". Screens are plain `lv.obj` instances.

```python
scr = lv.screen_active()      # current screen
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

new = lv.obj()                # a new screen (no parent)
lv.screen_load(new)           # switch to it (instant)
lv.screen_load_anim(new2, lv.SCREEN_LOAD_ANIM.MOVE_LEFT, 300, 0, True)
```

Layers sit above/below the screens: `lv.layer_top()`, `lv.layer_sys()`,
`lv.layer_bottom()`.

### 8.2 Creating objects

Widgets are created with the parent as their only positional argument:

```python
btn  = lv.button(scr)
lbl  = lv.label(btn)
```

### 8.3 Geometry

```python
obj.set_pos(x, y)
obj.set_size(w, h)
obj.align(lv.ALIGN.CENTER, 0, 0)          # align + (x, y) offset
obj.align_to(other, lv.ALIGN.OUT_RIGHT_MID, 8, 0)
obj.center()                              # shorthand for CENTER align
print(obj.get_width(), obj.get_height())
obj.set_x(10); obj.set_y(20)
obj.set_width(80); obj.set_height(40)
```

`lv.ALIGN.*`: `TOP_LEFT, TOP_MID, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_MID,
BOTTOM_RIGHT, LEFT_MID, RIGHT_MID, CENTER, OUT_TOP_LEFT … OUT_RIGHT_BOTTOM`.

### 8.4 Flags and state

```python
obj.add_flag(lv.obj.FLAG.HIDDEN)      # hide (use remove_flag to show)
obj.remove_flag(lv.obj.FLAG.CLICKABLE)
obj.add_state(lv.STATE.DISABLED)
```

Common flags: `HIDDEN`, `CLICKABLE`, `SCROLLABLE`, `CHECKABLE`, `PRESS_LOCK`,
`EVENT_BUBBLE`, `IGNORE_LAYOUT`.
> There is **no `clear_flag`** in this binding — use `remove_flag`.
> `lv.obj.FLAG.*` (not `lv.OBJ_FLAG.*`).

### 8.5 Colours and opacity

```python
lv.color_hex(0xFF0000)          # 0xRRGGBB -> colour
lv.color_make(255, 0, 0)        # from r, g, b
lv.color_white() / lv.color_black()
lv.palette_main(lv.PALETTE.BLUE)
lv.palette_lighten(lv.PALETTE.BLUE, 2)
lv.OPA.TRANSP / lv.OPA.COVER / lv.OPA._50
```

### 8.6 Text, fonts, symbols

```python
lbl.set_text('Hello')
lbl.set_style_text_font(lv.font_montserrat_16, 0)   # 12 / 14 / 16 available
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
```

Only `lv.font_montserrat_12`, `lv.font_montserrat_14`, `lv.font_montserrat_16`
are built in (plus `lv.font_get_default()`). Symbols such as `lv.SYMBOL.OK`,
`lv.SYMBOL.CLOSE`, `lv.SYMBOL.PLAY` can be used in text/labels.

### 8.7 Styling (see also [§11](#11-styles))

```python
obj.set_style_bg_color(lv.color_hex(0x202020), 0)
obj.set_style_bg_opa(lv.OPA.COVER, 0)
obj.set_style_radius(8, 0)
obj.set_style_border_width(0, 0)
obj.set_style_pad_all(8, 0)
```

### 8.8 Redrawing

LVGL redraws automatically inside the task handler. You can force it:

```python
obj.invalidate()
scr.invalidate()
```

### 8.9 The main loop

The frozen `TaskHandler` already calls `lv.tick_inc()` + `lv.task_handler()` on
a timer. When running a **script** (not the frozen app), you must keep the
interpreter alive so that loop can run — otherwise `mpremote run` exits and the
UI freezes. The idiomatic tail is:

```python
import lcd_bus, time
while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
```

`lcd_bus._pump_main_thread()` services the display/DMA + LVGL from the main
thread. (You can also call `lv.timer_handler()` yourself.)

### 8.10 Timers and animation

```python
def tick(t):
    print('tick')

timer = lv.timer_create(tick, 500, None)   # every 500 ms
timer.set_repeat_count(-1)                 # forever (-1) or a count
timer.delete()                             # stop it

anim = lv.anim_t()
anim.set_var(slider)
anim.set_values(0, 100)
anim.set_duration(800)
anim.set_path_cb(lv.anim_t.path_ease_in_out)
anim.start()
```

---

## 9. LVGL widgets

`parent` is always the first (positional) argument. Constructors take no other
arguments in this binding; configure the widget with methods afterwards.
Method arguments are **positional-only**.

### 9.1 `lv.obj` — base object / container / screen

```python
box = lv.obj(scr)
box.set_size(120, 80)
box.align(lv.ALIGN.CENTER, 0, 0)
box.set_style_bg_color(lv.color_hex(0x333333), 0)
box.set_style_radius(8, 0)
```

Key methods: `set_pos, set_size, set_x/y, set_width/height, align, align_to,
center, add_flag, remove_flag, add_state, remove_state, add_style,
set_style_*, set_scrollbar_mode, get_child, get_parent, delete, move_foreground,
move_background`.

### 9.2 `lv.label` — text

```python
lbl = lv.label(scr)
lbl.set_text('Line 1\nLine 2')
lbl.set_long_mode(lv.label.LONG_MODE.WRAP)
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.align(lv.ALIGN.TOP_LEFT, 8, 8)
```

Methods: `set_text, get_text, set_long_mode` (`lv.label.LONG_MODE.WRAP/DOTS/
SCROLL/SCROLL_CIRCULAR/CLIP`), `set_recolor`.

### 9.3 `lv.button` — clickable button

```python
btn = lv.button(scr)
btn.set_size(160, 60)
btn.align(lv.ALIGN.CENTER, 0, -40)
lbl = lv.label(btn)
lbl.set_text('CLICK ME')
lbl.center()

def on_click(e):
    if e.get_code() == lv.EVENT.CLICKED:
        print('clicked')

btn.add_event_cb(on_click, lv.EVENT.ALL, None)
```

`lv.button` has no own methods — use events.

### 9.4 `lv.slider` — value slider

```python
slider = lv.slider(scr)
slider.set_range(0, 100)
slider.set_value(50, 0)          # (value, anim_en)  — use 0, there is no ANIM_OFF
slider.set_size(220, 20)
slider.align(lv.ALIGN.CENTER, 0, 40)
print(slider.get_value())
```

Methods: `set_value(x, anim_en), get_value, set_range(min, max), set_min_value,
set_max_value, set_mode(lv.slider.MODE.NORMAL/SYMMETRICAL/RANGE),
set_orientation(lv.slider.ORIENTATION.HORIZONTAL/VERTICAL), is_dragged`.

### 9.5 `lv.switch` — on/off toggle

```python
sw = lv.switch(scr)
sw.align(lv.ALIGN.CENTER, 0, 0)

def on_sw(e):
    if e.get_code() == lv.EVENT.VALUE_CHANGED:
        on = sw.has_state(lv.STATE.CHECKED)
        print('switch is', 'ON' if on else 'OFF')

sw.add_event_cb(on_sw, lv.EVENT.ALL, None)
```

Read the state with `sw.has_state(lv.STATE.CHECKED)`; set it with
`sw.add_state` / `sw.remove_state`.

### 9.6 `lv.bar` — progress bar

```python
bar = lv.bar(scr)
bar.set_range(0, 100)
bar.set_value(30, 0)
bar.set_size(200, 16)
bar.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.7 `lv.arc` — arc / knob

```python
arc = lv.arc(scr)
arc.set_size(140, 140)
arc.set_bg_angles(0, 360)
arc.set_rotation(270)
arc.set_value(30)
arc.align(lv.ALIGN.CENTER, 0, 0)
print(arc.get_value())
```

### 9.8 `lv.checkbox`

```python
cb = lv.checkbox(scr)
cb.set_text('Enable')
cb.align(lv.ALIGN.TOP_LEFT, 12, 12)
```

### 9.9 `lv.dropdown`

```python
dd = lv.dropdown(scr)
dd.set_options('Red\nGreen\nBlue')
dd.set_selected(0)               # (index)
dd.align(lv.ALIGN.TOP_LEFT, 12, 12)
print(dd.get_selected())         # 0
print(dd.get_text())
```

### 9.10 `lv.roller`

```python
roller = lv.roller(scr)
roller.set_options('1\n2\n3\n4\n5', lv.roller.MODE.NORMAL)
roller.set_visible_row_count(3)
roller.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.11 `lv.textarea` — text input

```python
ta = lv.textarea(scr)
ta.set_one_line(True)
ta.set_placeholder_text('type here')
ta.set_max_length(32)
ta.set_size(200, 40)
ta.align(lv.ALIGN.CENTER, 0, 0)
# ta.get_text()
```

### 9.12 `lv.keyboard` — on-screen keyboard

```python
kb = lv.keyboard(scr)
kb.set_textarea(ta)              # type into the textarea
kb.set_mode(lv.keyboard.MODE.TEXT_LOWER)
```

`lv.keyboard.MODE`: `TEXT_LOWER, TEXT_UPPER, SPECIAL, NUMBER`.

### 9.13 `lv.table`

```python
tbl = lv.table(scr)
tbl.set_column_count(3)
tbl.set_row_count(3)
tbl.set_cell_value(0, 0, 'Name')
tbl.set_cell_value(0, 1, 'Value')
tbl.set_cell_value(1, 0, 'Temp')
tbl.set_cell_value(1, 1, '23')
tbl.set_size(280, 160)
tbl.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.14 `lv.tabview` — tabbed pages

```python
tv = lv.tabview(scr)
tab1 = tv.add_tab('Tab 1')
tab2 = tv.add_tab('Tab 2')
lv.label(tab1).set_text('page one')
lv.label(tab2).set_text('page two')
tv.set_active(0, 0)
```

### 9.15 `lv.chart` — graphs

```python
chart = lv.chart(scr)
chart.set_type(lv.chart.TYPE.LINE)
chart.set_point_count(20)
chart.set_axis_range(lv.chart.AXIS.PRIMARY_Y, 0, 100)
ser = chart.add_series(lv.palette_main(lv.PALETTE.BLUE), lv.chart.AXIS.PRIMARY_Y)
chart.set_next_value(ser, 42)     # push a new sample
chart.set_size(280, 150)
chart.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.16 `lv.spinner` — activity indicator

```python
sp = lv.spinner(scr)
sp.set_size(60, 60)
sp.set_anim_params(1000, 200)     # (time, delay)
sp.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.17 `lv.led`

```python
led = lv.led(scr)
led.set_color(lv.palette_main(lv.PALETTE.GREEN))
led.set_brightness(200)
led.on()
led.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.18 `lv.list` / `lv.list.add_button`

```python
lst = lv.list(scr)
lst.set_size(200, 160)
btn = lst.add_button(lv.SYMBOL.SETTINGS, 'Settings')
lst.add_text('About')
lst.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.19 `lv.msgbox`

```python
mb = lv.msgbox(scr)
mb.add_title('Confirm')
mb.add_text('Save changes?')
ok = mb.add_footer_button('OK')
mb.add_footer_button('Cancel')

def on_ok(e):
    if e.get_code() == lv.EVENT.CLICKED:
        print('OK pressed')

ok.add_event_cb(on_ok, lv.EVENT.CLICKED, None)
```

### 9.20 `lv.image` / `lv.imagebutton` / `lv.animimg`

```python
img = lv.image(scr)          # set the source later: img.set_src(...)
ib  = lv.imagebutton(scr)    # ib.set_src(state, left, mid, right)
an  = lv.animimg(scr)        # an.set_src(dsc, count); an.start()
```

> Image sources in this binding require an LVGL image descriptor. This is an
> advanced topic; the widget methods (`set_src`, `set_scale`, `set_rotation`,
> `set_offset_x/y`, `set_pivot`) are available.

### 9.21 Other widgets available

`lv.win`, `lv.menu` / `lv.menu_page`, `lv.line`, `lv.scale`, `lv.spinbox`,
`lv.spangroup`, `lv.tileview`, `lv.calendar`, `lv.buttonmatrix`, `lv.arclabel`.
The complete list and every method is in `lvgl.pyi` in the source repository.

---

## 10. Events

Attach a callback with `add_event_cb(callback, filter, user_data)`:

```python
def handler(e):
    code = e.get_code()
    if code == lv.EVENT.CLICKED:
        print('clicked, target:', e.get_target_obj())
        print('user data:', e.get_user_data())

obj.add_event_cb(handler, lv.EVENT.ALL, some_data)
```

- `filter` is usually `lv.EVENT.ALL` or one specific code.
- `user_data` is returned by `e.get_user_data()`.

### 10.1 Common event codes

| Code | Fires when |
| --- | --- |
| `lv.EVENT.PRESSED` | pointer pressed on the object |
| `lv.EVENT.PRESSING` | pointer is being held/dragged |
| `lv.EVENT.RELEASED` | pointer released |
| `lv.EVENT.CLICKED` | a click completed |
| `lv.EVENT.LONG_PRESSED` | held for a long time |
| `lv.EVENT.VALUE_CHANGED` | value changed (slider, switch, arc, …) |
| `lv.EVENT.SCROLL_BEGIN` / `SCROLL_END` | scrolling |
| `lv.EVENT.SCREEN_LOADED` / `SCREEN_UNLOADED` | screen switched |
| `lv.EVENT.DELETE` | the object is being deleted |
| `lv.EVENT.ALL` | wildcard — all events |

### 10.2 Event object methods

| Method | Returns |
| --- | --- |
| `e.get_code()` | the event code |
| `e.get_target_obj()` | the object that triggered it (use this) |
| `e.get_current_target_obj()` | the object the callback is attached to |
| `e.get_user_data()` | the `user_data` passed to `add_event_cb` |
| `e.get_target()` | opaque value — prefer `get_target_obj()` |

> In this binding `e.get_target()` returns an opaque blob without widget
> methods. Use `e.get_target_obj()`, or close over the widget variable.

### 10.3 Reading the touch point in a callback

```python
def on_event(e):
    if e.get_code() == lv.EVENT.PRESSING:
        pt = lv.point_t()
        board.touch.get_point(pt)
        print(pt.x, pt.y)
```

---

## 11. Styles

Two ways to style: set properties directly on an object, or build a reusable
`lv.style_t` and add it.

### 11.1 Direct (most common)

```python
obj.set_style_bg_color(lv.color_hex(0x202020), 0)
obj.set_style_bg_opa(lv.OPA.COVER, 0)
obj.set_style_radius(8, 0)
obj.set_style_border_width(2, 0)
obj.set_style_border_color(lv.color_hex(0xFFFFFF), 0)
obj.set_style_pad_all(8, 0)
obj.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
obj.set_style_text_font(lv.font_montserrat_14, 0)
```

The second argument is the **selector** (`lv.PART.* | lv.STATE.*`). `0` means
`PART.MAIN` in the default state. Examples: `lv.PART.INDICATOR | lv.STATE.PRESSED`.

### 11.2 Reusable style objects

```python
style = lv.style_t()
style.init()
style.set_bg_color(lv.color_hex(0x004080))
style.set_bg_opa(lv.OPA.COVER)
style.set_radius(6)
style.set_pad_all(10)

btn.add_style(style, 0)
btn.remove_style(style, 0)
```

### 11.3 Common `set_style_*` properties on objects

Background: `bg_color, bg_opa, bg_grad_color, bg_grad_dir`.
Border: `border_color, border_width, border_opa, border_side`.
Outline: `outline_color, outline_width, outline_pad`.
Shadow: `shadow_color, shadow_width, shadow_offset_x/y, shadow_spread`.
Text: `text_color, text_font, text_letter_space, text_line_space, text_align`.
Size/space: `width, height, min_width, max_width, radius, pad_all, pad_hor,
pad_ver, pad_left/right/top/bottom, margin_all, x, y`.
Misc: `opa, clip_corner, transform_scale, transform_rotation, blend_mode,
recolor, recolor_opa`.

`lv.RADIUS_CIRCLE` (= 32767) makes a fully round object (not `lv.RADIUS.CIRCLE`).

---

## 12. System modules

### 12.1 `machine` — pins, buses, timers

```python
import machine
p = machine.Pin(21, machine.Pin.OUT)
p.value(1)
pwm = machine.PWM(p, freq=38000)
pwm.duty_u16(32768)

spi = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
tim = machine.Timer(0)
```

### 12.2 `network` — Wi-Fi

```python
import network

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect('SSID', 'password')          # STA connect
# sta.ifconfig()                         # (ip, netmask, gateway, dns)
# sta.isconnected()

ap = network.WLAN(network.AP_IF)         # hosted access point
ap.active(True)
ap.config(essid='CYD', password='12345678')
```

Scan example (see [§13.6](#136-wi-fi-scan)):

```python
for ssid, bssid, ch, rssi, sec, hidden in sta.scan():
    print(ssid, rssi, ch)
```

### 12.3 `time`, `machine.Timer`, `gc`

```python
import time, gc
time.sleep(1); time.sleep_ms(10); time.sleep_us(100)
time.ticks_ms(); time.ticks_diff(t2, t1)
gc.collect(); gc.mem_free()
```

### 12.4 `esp32`

```python
import esp32
esp32.raw_temperature()      # internal temp (F)
esp32.wake_on_touch(True)
```

---

## 13. Complete example programs

Save any of these and run with `mpremote run <file>`, or use `tests/run.sh`.

### 13.1 Hello, CYD

```python
import lvgl as lv, lcd_bus, time
import display                       # brings the board up

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x001030), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

lbl = lv.label(scr)
lbl.set_text('Hello, CYD!')
lbl.set_style_text_font(lv.font_montserrat_16, 0)
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.center()
scr.invalidate()

while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
```

### 13.2 Button counter

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x101018), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

count = 0
cl = lv.label(scr); cl.set_text('taps: 0'); cl.align(lv.ALIGN.TOP_MID, 0, 10)

def on_btn(e):
    global count
    if e.get_code() == lv.EVENT.CLICKED:
        count += 1
        cl.set_text('taps: %d' % count)

btn = lv.button(scr); btn.set_size(160, 60); btn.align(lv.ALIGN.CENTER, 0, 0)
lv.label(btn).set_text('TAP ME')
btn.add_event_cb(on_btn, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.3 Slider drives a bar

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

bar = lv.bar(scr); bar.set_range(0, 100); bar.set_value(0, 0)
bar.set_size(240, 20); bar.align(lv.ALIGN.CENTER, 0, -40)

slider = lv.slider(scr); slider.set_range(0, 100); slider.set_value(0, 0)
slider.set_size(240, 20); slider.align(lv.ALIGN.CENTER, 0, 20)

def on_slider(e):
    if e.get_code() == lv.EVENT.VALUE_CHANGED:
        bar.set_value(slider.get_value(), 0)

slider.add_event_cb(on_slider, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.4 Switch changes a colour box

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

box = lv.obj(scr); box.set_size(100, 100); box.align(lv.ALIGN.CENTER, 0, -40)
box.set_style_bg_opa(lv.OPA.COVER, 0); box.set_style_radius(8, 0)
box.set_style_bg_color(lv.color_hex(0x444444), 0)

sw = lv.switch(scr); sw.align(lv.ALIGN.CENTER, 0, 50)

def on_sw(e):
    if e.get_code() == lv.EVENT.VALUE_CHANGED:
        if sw.has_state(lv.STATE.CHECKED):
            box.set_style_bg_color(lv.color_hex(0x00C000), 0)
        else:
            box.set_style_bg_color(lv.color_hex(0x444444), 0)
        box.invalidate()

sw.add_event_cb(on_sw, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.5 Draw a dot under your finger

```python
import lvgl as lv, lcd_bus, time
import board

board.calibrate_touch()
W, H = board.size()
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

dot = lv.obj(scr); dot.set_size(28, 28)
dot.set_style_bg_color(lv.color_hex(0x00FF00), 0)
dot.set_style_bg_opa(lv.OPA.COVER, 0)
dot.set_style_radius(lv.RADIUS_CIRCLE, 0)
dot.set_style_border_width(0, 0)
dot.add_flag(lv.obj.FLAG.HIDDEN)

def on_event(e):
    code = e.get_code()
    if code == lv.EVENT.PRESSING:
        pt = lv.point_t()
        board.touch.get_point(pt)
        dot.set_pos(pt.x - 14, pt.y - 14)
        dot.remove_flag(lv.obj.FLAG.HIDDEN)
    elif code == lv.EVENT.RELEASED:
        dot.add_flag(lv.obj.FLAG.HIDDEN)

area = lv.obj(scr); area.set_size(W, H); area.set_pos(0, 0)
area.set_style_bg_opa(lv.OPA.TRANSP, 0)
area.set_style_border_width(0, 0)
area.add_flag(lv.obj.FLAG.CLICKABLE)
area.add_event_cb(on_event, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.6 Wi-Fi scan

```python
import network

sta = network.WLAN(network.STA_IF)
sta.active(True)
print('scanning...')
for ssid, bssid, ch, rssi, sec, hidden in sorted(sta.scan(), key=lambda n: n[3], reverse=True):
    print('%-24s %4d dBm  ch %d' % (
        ssid.decode() if isinstance(ssid, bytes) else ssid, rssi, ch))
```

### 13.7 Tabs with a slider and a button

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

tv = lv.tabview(scr)
p1 = tv.add_tab('Slider')
p2 = tv.add_tab('Button')

s = lv.slider(p1); s.set_range(0, 100); s.set_value(10, 0)
s.set_width(200); s.center()

b = lv.button(p2); b.set_size(140, 50); b.center()
lv.label(b).set_text('PRESS')

def on_b(e):
    if e.get_code() == lv.EVENT.CLICKED:
        print('pressed on tab 2')
b.add_event_cb(on_b, lv.EVENT.ALL, None)

scr.invalidate()
while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

---

## 14. Binding quirks & gotchas

| Topic | Correct usage | Not this |
| --- | --- | --- |
| Object flags | `lv.obj.FLAG.HIDDEN`, `add_flag` / `remove_flag` | `lv.OBJ_FLAG.*`, `clear_flag` |
| Round radius | `lv.RADIUS_CIRCLE` | `lv.RADIUS.CIRCLE` |
| Slider value | `slider.set_value(v, 0)` | `lv.ANIM_OFF` (does not exist) |
| Calls inside event cb | `board.touch.get_point(pt)` | `lv.indev_active()` (may be `None`) |
| Event target | `e.get_target_obj()` | `e.get_target()` (opaque) |
| Older examples | `lv.img`, `lv.imgbtn` | use `lv.image`, `lv.imagebutton` (LVGL 9 names) |
| Meter | — | `lv.meter` does not exist (LVGL 9 uses `lv.scale`) |
| Indev creation | `import display` (once per power cycle) | re-`import display` after soft reset |

- Constructor arguments are **positional-only**; parameter *names* in the stub
  are auto-generated and sometimes meaningless. Use positional calls.
- LVGL 9 renamed several things vs older tutorials: `lv.image` (was `lv.img`),
  `lv.imagebutton` (was `lv.imgbtn`), `lv.spangroup` (was `lv.span`).
- Only Montserrat 12/14/16 fonts are compiled in.

---

## 15. Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `TypeError: can't convert str to int` in `display.py` | Re-importing `display` in the same power cycle. Hard-reset the board first. |
| Screen is black | Backlight at 0 — call `board.backlight(100)`. Check the flash succeeded. |
| Colours wrong (red shows blue) | The image was built without BGR; use the provided `firmware/*.bin`. |
| Image skewed / black band / mirrored | Wrong `_ORIENTATION_TABLE` / `display_width`; use the provided firmware. |
| Touch is off by ~80 px | Calibration fitted to screen instead of pre-rotation coordinate; use `board.calibrate_touch()`. |
| Touch does nothing | Not calibrated (`board.touch.is_calibrated`) or `touch.enable(True)` missing. |
| UI freezes right after script ends | `mpremote run` returned. Add the `while True: lcd_bus._pump_main_thread()` loop. |
| `MemoryError` | The app partition is full; reduce widgets/features and rebuild. |
| `AttributeError` on a widget method | Name differs in this binding — check `lvgl.pyi`. |

---

## 16. The test suite

`tests/` contains standalone scripts (not built into the firmware). Use the
wrapper, which hard-resets the board first (required, see [§4](#4-the-frozen-display-module)):

```bash
cd tests
./run.sh boot_check.py       # smoke test
./run.sh test_pattern.py     # coverage / orientation / colours
./run.sh test_display.py
./run.sh test_backlight.py
./run.sh test_touch.py       # needs taps
./run.sh test_lvgl.py        # needs taps
./run.sh test_wifi.py
```

Set the port if needed:

```bash
CYD_PORT=/dev/cu.usbserial-0001 ./run.sh test_display.py
```

Interactive tests (`test_touch.py`, `test_lvgl.py`) end in a polling loop so
LVGL keeps running; stop with `Ctrl-C`.

---

## 17. Rebuilding the firmware

See the build guides in the source repository:

- `lvgl_micropython/AGENTS.md` — full build/TOML/flashing detail.
- `AGENTS.md` (repo root) — project overview and gotchas.

Build command (takes ~15–30 min the first time):

```bash
python3 make.py esp32 --toml display_configs/CYD-2432S028R.toml --ccache --no-scrub
```

Output: `build/lvgl_micropy_ESP32_GENERIC-4.bin` (flash at `0x0`).

---

*MicroPython 1.27.0 · LVGL 9.4.0 · ESP-IDF 5.5.1 · board ESP32-2432S028R.*
