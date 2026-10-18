# AGENTS.md

Guidance for opencode agents working in this repository.

## Project overview

This repo builds a **MicroPython + LVGL** firmware image for the
**ESP32 Cheap Yellow Display (CYD), classic board ESP32-2432S028R**
(ESP32-WROOM-32, 4 MB flash, no PSRAM, ILI9341 240x320 portrait panel driven as 320x240
landscape via rotation, XPT2046 touch).

Top-level directories:

- `lvgl_micropython/` - the build system (upstream `lvgl-micropython/lvgl_micropython`, branch `main`).
  Contains `make.py`, `builder/`, `display_configs/`, the target config
  `display_configs/CYD-2432S028R.toml`, and the `build.sh` variant wrapper.
  The detailed, verified build guide lives in `lvgl_micropython/AGENTS.md` - read it before changing the build.
- `tests/` - standalone board test scripts and the Thai shaper (`thai.py`), run over serial with `tests/run.sh`.
- `firmware/` - prebuilt images, split by language (`en/`, `th/`) and flashing tool
  (`esptool-0x0/`, `thonny-0x1000/`).
- `docs/` - user manual (English / Thai).
- `ESP32-Cheap-Yellow-Display/` - CYD hardware docs and pinout reference only (no build here).

## Build (run from `lvgl_micropython/`)

There are **two firmware variants**, selected by a single TinyTTF define. Use the wrapper:

```bash
cd lvgl_micropython
./build.sh en     # English only  - TinyTTF disabled, ~2.94 MB  -> build/lvgl_micropy_CYD-en.bin
./build.sh th     # English+Thai  - TinyTTF enabled,  ~3.00 MB  -> build/lvgl_micropy_CYD-th.bin
```

`build.sh` just runs `make.py esp32 [LV_CFLAGS=...] --toml display_configs/CYD-2432S028R.toml
--ccache --no-scrub` and copies the merged image to a variant-named file. The equivalent raw
command is:

```bash
python3 make.py esp32 --toml display_configs/CYD-2432S028R.toml --ccache --no-scrub
# TH variant only: add  LV_CFLAGS=-DMICROPY_TINY_TTF=1  as the 2nd argument
```

- The **only** difference is `MICROPY_TINY_TTF`, which `lib/lv_conf.h` maps to
  `LV_USE_TINY_TTF`. Pass it via `LV_CFLAGS` (never by editing `lv_conf.h`) so that both the
  C compile *and* the LVGL MicroPython binding generator (`ext_mod/lvgl/micropython.cmake`
  passes `${LV_CFLAGS}` to the generator) see it. Verified: the EN binding has no
  `tiny_ttf_*` symbols, the TH binding has 8.
- Slow (~15-30 min first run): ESP-IDF v5.5.1 + tools are auto-installed to `~/.espressif/`,
  then ~2400 compile targets, and a second pass if the app partition auto-resizes.
- Run it in the background and poll `/tmp/cyd_build.log` if working under a short tool timeout.
- Output: `lvgl_micropython/build/lvgl_micropy_ESP32_GENERIC-4.bin` (~2.9 MB merged image),
  copied by `build.sh` to `build/lvgl_micropy_CYD-<variant>.bin`.

## Flash

The exact esptool command is printed at the end of a successful build. The merged bin
flashes at **`0x0`** (not `0x1000`). Replace `(PORT)` with the macOS serial device
(`/dev/cu.usbserial-*`, `/dev/cu.wchusbserial*`):

```bash
~/.espressif/python_env/idf5.5_py3.13_env/bin/python -m esptool \
  --chip esp32 -p (PORT) -b 460800 --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m --erase-all \
  0x0 lvgl_micropython/build/lvgl_micropy_ESP32_GENERIC-4.bin
```

## Key facts / gotchas

- Classic CYD has **no PSRAM**: keep `BOARD_VARIANT=SPIRAM` disabled in the TOML.
- `backlight_on_state` must match the actual display driver (`ili9341.STATE_PWM`), not `st7789`.
- **Display is portrait-native**: use `display_width/height = 240/320` + `set_rotation._90`
  (landscape 320x240), and `_ORIENTATION_TABLE = [64, 32, 128, 224]` (0x40, 0x20, 0x80, 0xE0;
  BGR bit `0x08` is OR'd in at runtime). Two rotations 180 apart differ by XOR `0xC0` and the
  MV bit `0x20` marks landscape, so index 1 = `0x20` (MV only) and index 3 = `0xE0` (MV|MX|MY).
  The upstream `320/240` + `[0, 96, 192, 160]` gives a skewed/black-banded and mirrored image;
  the older `[0, 32, 192, 160]` mirrored `_0` and `_270`. Verify all four with
  `tests/test_pattern.py` / `tests/test_rotation.py`.
- **Panel is BGR**: set `color_byte_order = "ili9341.BYTE_ORDER_BGR"` in `[ILI9341.display]`.
  The default RGB leaves the image upright but **swaps red/blue** (a drawn red band shows
  blue). BGR makes landscape MADCTL `0x28` (`0x20 | 0x08`), matching TFT_eSPI's CYD.
- **Touch calibration**: the frozen `indev.calibrate()` is broken for this board (it forces
  rotation `_0` while sizing targets from the landscape `_orig_width/_orig_height`, so the
  targets land off-screen). `tests/board.py:calibrate_touch()` runs a 5-point least-squares
  calibration in landscape instead. It must fit raw -> the **pre-rotation** coordinate:
  LVGL applies `disp->rotation` to pointer points a second time
  (`lib/lvgl/src/indev/lv_indev.c:693`), using the *unrotated* internal `ver_res` (320, not
  the reported 240), so the `_90` target is `(ty, 319 - tx)`. Fitting `raw -> screen`
  directly is ~80px off. Verified: `get_point` within ~6px at all corners + centre.
- The app partition is ~99.9% full (~3.9 KB free). Enable `optimize_size = true` in the TOML
  before adding features. "app partition is too small" during the first ESP-IDF pass is normal
  (triggers an auto-resize + second pass), not an error.
- `lib/*` submodules (esp-idf, lvgl, micropython, pycparser) are cloned automatically by the
  builder. Do **not** run `git submodule update --init` manually.
- Host python (tested 3.13.11) drives `make.py`; ESP-IDF uses its own venv. Only fall back to
  Homebrew `python3.11` if the toolchain install fails.

## Board tests (`tests/`)

Standalone MicroPython scripts (not part of the firmware) live in `tests/`. Run them with
the wrapper, which hard-resets the board first:

```bash
cd tests
./run.sh boot_check.py      # smoke test
./run.sh test_pattern.py    # full coverage / orientation / colours
./run.sh test_rotation.py   # cycle all 4 rotations, check none is mirrored
./run.sh test_display.py
./run.sh test_touch.py
./run.sh test_lvgl.py
./run.sh test_thai.py       # shaped Thai vs unshaped (needs the TH firmware + font)
./run.sh test_thai_sizes.py # sweep 24/22/20/18/16/14 px on one screen
./run.sh test_wifi.py
```

`run.sh` also copies `tests/thai.py` to the board if present.

- `tests/board.py` does `import display` (the frozen module that brings up ILI9341 + XPT2046).
- **Hard reset is required before each run**: mpremote soft-resets on connect, but an ESP32
  SPI host created by `import display` survives a soft reset, so re-creating the bus fails
  with `TypeError: can't convert str to int`. `run.sh` does the DTR/RTS reset.
- Touch scripts need physical taps for calibration; see `tests/README.md`.
- **Interactive tests must keep running**: `mpremote run` exits as soon as the script's
  top-level code returns, which stops the LVGL loop. `test_touch.py` / `test_lvgl.py` end in
  a `while True: lcd_bus._pump_main_thread()` loop so the dot/widgets keep responding.
- **LVGL binding quirks** seen here:
  `lv.indev_active()` returns `None` inside event callbacks - read the point with
  `board.touch.get_point(pt)` instead. Objects use `add_flag` / `remove_flag` (no
  `clear_flag`). `e.get_target()` returns an opaque `Blob`; use the widget object directly
  (e.g. `slider.get_value()`) or `e.get_target_obj()`.

## Thai text (TTF + minimal shaper)

LVGL 9.4 has **no OpenType shaping** (no HarfBuzz/GPOS), so Thai combining marks
(a tone above an upper vowel, e.g. `ดี้`) are drawn at their default offsets and overlap.
Thai support is therefore a runtime concern, not a build one:

- **Only the TH variant** (`./build.sh th`) has TinyTTF. In firmware it is used through
  LVGL: `lv.tiny_ttf_create_file_ex(path, size, lv.FONT_KERNING.NONE, cache)`.
- The shaper is `tests/thai.py`: it clusters Thai text, re-stacks upper marks using real
  glyph metrics from `lv.font_t.get_glyph_dsc`, and renders with one `lv.label` per run of
  "base width" glyphs plus a raised label per upper mark. Verified on hardware.
- **Font size**: TinyTTF rasterises the TTF on the fly, so `ThaiFont(path, size)` accepts any
  pixel size with no rebuild/flash. Verified legible and correctly stacked from **14 px**
  (line_height 18) up to 24 px; `tests/test_thai.py` uses **14** by default and
  `tests/test_thai_sizes.py` sweeps 24/22/20/18/16/14 on one screen for comparison. Cache
  memory depends on the number of distinct glyphs, not the size.
- It relies on LVGL geometry (`lib/lvgl/src/draw/lv_draw_label.c`):
  `glyph_top = pos.y + (line_height - base_line) - box_h - ofs_y`, so `ofs_y` is the
  distance from the baseline up to the glyph's *bottom* edge; a mark is raised by moving
  its label up. Kerning is disabled so the shaper's pen maths match LVGL's layout.
- `lv.LV_FONT_KERNING` is exposed as **`lv.FONT_KERNING`** (no `LV_` prefix).
- The font and `thai.py` live on the board filesystem (the app partition is ~99.9% full,
  so they cannot be frozen). Copy them with:
  `mpremote connect PORT fs cp tests/thai.py :thai.py` and
  `mpremote connect PORT fs cp tests/fonts/Sarabun-Regular.ttf :Sarabun-Regular.ttf`,
  then register a letter-`A` FS driver before creating the font:
  `import fs_driver; fs_driver.fs_register(lv.fs_drv_t(), "A")` (must come *after*
  `import display`, which calls `lv.init()`).

## Conventions

- Do not commit or flash unless explicitly asked.
- After changing build config, keep `lvgl_micropython/AGENTS.md` and this file in sync.
