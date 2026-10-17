# CYD board test programs

Standalone MicroPython scripts for testing the **ESP32 Cheap Yellow Display
(CYD) classic ESP32-2432S028R** that this project targets. They run on the
board over USB serial — nothing here is built into the firmware, so you can
edit and re-run them freely.

## Prerequisite

The firmware must already be flashed (with the working `display` module), and
the device plugged in over USB. Check the port with `ls /dev/cu.*` — on this
machine it is `/dev/cu.wchusbserial2110`.

Quick smoke test:

```bash
cd tests
./run.sh boot_check.py
```

You should see a board-info dump, the screen flashing white / grey / black,
and `boot_check OK`.

To confirm the panel is wired up correctly (full coverage, upright, colours),
run the pattern test and compare against the screen:

```bash
./run.sh test_pattern.py
```

The image should cover the whole 320x240 panel with a white border and yellow
crosshair, `TOP` at the top, and corner blocks top-left=white, top-right=red,
bottom-left=green, bottom-right=blue.

## Running a test

Use the included `run.sh` wrapper:

```bash
./run.sh test_display.py
./run.sh test_backlight.py
./run.sh test_touch.py
./run.sh test_lvgl.py
./run.sh test_wifi.py
```

Set `CYD_PORT` if your port differs:

```bash
CYD_PORT=/dev/cu.usbserial-0001 ./run.sh test_display.py
```

### Why a wrapper (important)

`mpremote` **soft-resets** the board every time it connects. On the ESP32, an
SPI host created by `import display` is *not* released by a soft reset, so
re-running any test in the same power cycle fails inside `display.py` with a
confusing `TypeError: can't convert str to int` when it re-creates the SPI bus.

`run.sh` performs a **real** (DTR/RTS) reset before each run, which clears the
SPI host and makes every run start cleanly. If you run `mpremote` directly,
include a hard reset first, e.g. `mpremote connect PORT reset`
then `mpremote connect PORT run test_display.py`.

Under the hood the wrapper does, for a given script:

```bash
# 1. hard reset via DTR/RTS
# 2. copy board.py onto the device
mpremote connect PORT cp tests/board.py :board.py
# 3. run the script
mpremote connect PORT run tests/<script>.py
```

## Tooling

`mpremote` and `pyserial` are required:

```bash
pip install mpremote pyserial
```

Note: `mpremote` does **not** take `--port`; use `connect <port>` or the
`run.sh` wrapper. `mpremote connect PORT repl` gives an interactive prompt
(Ctrl-] to exit).

## The tests

| Script | What it verifies | Needs touch? |
| ------ | ---------------- | ------------ |
| `boot_check.py` | imports hardware, firmware info, backlight + colour flash | no |
| `test_pattern.py` | full-panel coverage, orientation, corner colours | no |
| `test_display.py` | ILI9341 panel: colour fills then R/G/B bars | no |
| `test_backlight.py` | PWM backlight fade 0–100% | no |
| `test_touch.py` | XPT2046 calibration + live coordinates + tracking dot | yes |
| `test_lvgl.py` | LVGL widgets (button / slider / label) + input | yes |
| `test_wifi.py` | ESP32 Wi-Fi radio scan (does not connect) | no |

Stop a script that loops (like `test_touch.py`) with `Ctrl-C`, or press
`Ctrl-D` to soft-reboot the board.

## Shared helper

Every test starts with `import board`. `board.py` does `import display`, which
brings up the panel + touch (the frozen `display` module wires the ILI9341 and
XPT2046 from the TOML config), and exposes:

- `board.lcd` — the ILI9341 display driver
- `board.touch` — the XPT2046 pointer driver
- `board.width()` / `board.height()` / `board.size()`
- `board.backlight(0..100)`
- `board.calibrate_touch(force=False)` — interactive landscape calibration
- `board.reset_touch_cal()` — erase the stored calibration
- `board.dump_info()` — print firmware/board report

## Touch calibration

`test_touch.py` (and `test_lvgl.py`) run `board.calibrate_touch()` first. If the
board has not been calibrated, a red square is shown at four corners and the
centre; tap each one when prompted. A least-squares affine fit is saved to NVS
(via `touch_cal_data`), so it only happens once. Force a re-calibration with
`board.calibrate_touch(force=True)`; erase it with `board.reset_touch_cal()`.

The frozen `indev.calibrate()` is **not** used: it forces the display to
rotation `_0` while sizing targets from the landscape `_orig_width/_orig_height`
(320x240), so its targets land off-screen. `board.calibrate_touch()` runs in the
real landscape rotation instead.

One subtlety it has to get right: LVGL rotates pointer points a *second*
time in `indev_pointer_proc` (`lib/lvgl/src/indev/lv_indev.c`), using the
unrotated internal `ver_res` (320). So the fit targets the pre-rotation
coordinate via `_lvgl_rotation_inverse()` - for rotation `_90` that is
`(ty, 319 - tx)`. Fitting `raw -> screen` directly is ~80px off. After the
fix, `get_point` is within ~6px of the actual tap.

Because calibration and touch reading need a person to tap the panel, these two
scripts cannot be fully verified head-less. They also end in a polling loop so
the LVGL loop keeps running after `mpremote run` would otherwise return.

## LVGL API notes (this binding)

A few names differ from stock LVGL examples:

- flags: `lv.obj.FLAG.HIDDEN` (not `lv.OBJ_FLAG.HIDDEN`); use `add_flag` /
  `remove_flag` — there is no `clear_flag`
- circle radius: `lv.RADIUS_CIRCLE` (not `lv.RADIUS.CIRCLE`)
- inside an event callback `lv.indev_active()` returns `None`; read the point
  from the driver instead: `board.touch.get_point(pt)`
- `e.get_target()` returns an opaque `Blob` with no widget methods — use
  `e.get_target_obj()` or keep a reference to the widget (`slider.get_value()`)
- no animation: pass `0` as the `anim_en` argument (`lv.ANIM_OFF` is absent)

## Adding a test

Create `tests/test_<name>.py`, `import board`, and drive the hardware. Keep
long-running loops interruptible with `Ctrl-C`. See the AGENTS.md files in the
repo root and `lvgl_micropython/` for the build/hardware details.
