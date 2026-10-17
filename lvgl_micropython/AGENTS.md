# AGENTS.md - lvgl_micropython build guide for ESP32 CYD

Build MicroPython + LVGL bindings for the **ESP32 Cheap Yellow Display (CYD)**
classic board **ESP32-2432S028R**.

## Target hardware (classic 2432S028R)

- MCU: ESP32-WROOM-32 (dual-core Xtensa), **4 MB flash, NO PSRAM**
- Display: ILI9341, **native 240x320 portrait**, driven as **320x240 landscape** via
  `set_rotation._90`. SPI. MOSI=13, MISO=12, SCK=14, CS=15, DC=2, BL=21, RST=none
- Touch: XPT2046, SPI. MOSI=32, MISO=39, SCK=25, CS=33, IRQ=36
- Boards with a different chip (e.g. ESP32-S3) need a different BOARD/config - this guide is only for the classic ESP32 CYD.

## Environment (macOS, verified)

- Working dir: `lvgl_micropython/`
- Python: system/conda `python3` (tested 3.13.11). The builder invokes ESP-IDF which
  creates its own venv at `~/.espressif/python_env/idf5.5_py3.13_env`. If a Python
  incompatibility appears, retry with Homebrew `python3.11`.
- Requires `cmake`, `ninja`, and Xcode CLT (present at `/opt/homebrew/bin` on this machine).
- Python dep: `toml` for the host (`pip3 install toml`). This is only used by the TOML reader.
- ESP-IDF **v5.5.1** and all tools are installed automatically on first build into
  `~/.espressif/` (xtensa-esp-elf 14.2.0, riscv32-esp-elf 14.2.0, esp-rom-elfs, openocd, gdb, esptool 4.12.0, etc.). First build downloads several hundred MB.

## Config: `display_configs/CYD-2432S028R.toml`

This is the tailored config for the classic CYD. Key points (already applied):

- `BOARD = "ESP32_GENERIC"` with `BOARD_VARIANT=SPIRAM` **commented out** (no PSRAM).
  The SPIRAM variant is safe (MicroPython sets `CONFIG_SPIRAM_IGNORE_NOTFOUND=y`) but
  adds overhead, so the plain variant is preferred here.
- `flash_size = 4`, `ccache = true`.
- `backlight_on_state = "ili9341.STATE_PWM"` (must match the `[ILI9341.display]` driver;
  a `st7789.*` value here wrongly pulls in the st7789 driver and bloats the image).
- `[display.init] params = [1]` (init type 1 = standard ILI9341 sequence) and
  `[display.set_backlight] params = [100]`. Do **not** use `params = []`: that maps to
  init `type=None`, which makes the driver `import _ili9341_init` (no such module) and
  fails. Only `_ili9341_init_type1` / `_ili9341_init_type2` exist.
- `[XPT2046.indev]` must be **uppercase**. The TOML reader lowercases the section name to
  find the module but keeps the name as the class, so `[xpt2046.indev]` emits
  `xpt2046.xpt2046(...)` (AttributeError). `[XPT2046.indev]` emits the correct
  `xpt2046.XPT2046(...)`.
- `[display._ORIENTATION_TABLE] value = [64, 32, 128, 224]`. This is indexed by rotation
  and each entry is the ILI9341 MADCTL byte for that rotation (the BGR bit `0x08` is OR'd in
  at runtime by `color_byte_order`). The rule: two rotations 180 degrees apart differ by XOR
  `0xC0` (toggle MX|MY), and the `MV` bit (`0x20`) marks landscape (`_90`/`_270`) vs portrait
  (`_0`/`_180`). So index 0 = `0x40` (`MX`), index 1 = `0x20` (`MV`), index 2 = `0x80` (`MY`,
  = `0x40 ^ 0xC0`) and index 3 = `0xE0` (`MV|MX|MY`, = `0x20 ^ 0xC0`). All four are upright.
  The stock value `[0, 96, 192, 160]` renders a **mirrored** image; the older
  `[0, 32, 192, 160]` left `_0` and `_270` mirrored. Do not use those for the CYD.
- `[ILI9341.display] display_width = 240`, `display_height = 320`: these are the
  **native/rotation-0** dimensions and must match the portrait-native `_ORIENTATION_TABLE`.
  Do **not** set 320x240 here - the driver renders 320 wide but the panel (MADCTL without
  MV) scans 240 wide, so the column window overruns -> skewed image with a black band.
- `[ILI9341.display] color_byte_order = "ili9341.BYTE_ORDER_BGR"`: the classic CYD panel
  is wired **BGR**; the driver default (RGB) swaps red/blue (a drawn red band shows blue).
  BGR adds MADCTL bit `0x08`, so landscape (rotation `_90`) becomes `0x20 | 0x08 = 0x28`,
  matching TFT_eSPI's CYD landscape. Verified on hardware.
- `[display.set_rotation] params = ["lv.DISPLAY_ROTATION._90"]` gives the classic CYD
  landscape 320x240 (so `board.size()` / `get_horizontal_resolution()` return 320x240).
- `optimize_size = true` is commented out; enable it if the image gets too large (see Size).

## Config deltas vs upstream (`display_configs/CYD-2432S028R.toml`)

The upstream file (last touched in commit `af63204`) needs the following edits for the
classic CYD. `upstream -> here -> why`:

| Key | Upstream | Here | Why |
| --- | --- | --- | --- |
| `BOARD_VARIANT` | `"SPIRAM"` | commented out | classic CYD has no PSRAM |
| `flash_size` | (unset) | `4` | 4 MB flash |
| `ccache` | (unset) | `true` | faster rebuilds |
| `ILI9341.display.display_width/height` | `320 / 240` | `240 / 320` | panel is portrait-native; the address window overruns otherwise |
| `backlight_on_state` | `st7789.STATE_PWM` | `ili9341.STATE_PWM` | match the actual driver |
| `color_byte_order` | (unset = RGB) | `ili9341.BYTE_ORDER_BGR` | CYD panel is BGR; RGB swaps red/blue |
| `_ORIENTATION_TABLE` | `[0, 96, 192, 160]` | `[64, 32, 128, 224]` | `MV` marks landscape, 180-degree pairs differ by `0xC0`; all four rotations upright |
| `display.set_rotation` | (absent) | `lv.DISPLAY_ROTATION._90` | gives landscape 320x240 |
| indev section name | `[xpt2046.indev]` | `[XPT2046.indev]` | TOML reader needs the class name, case-sensitive |

Unchanged from upstream: the SPI bus pins, `[display.init] params = [1]`,
`[display.set_backlight] params = [100]`, `color_space` and `rgb565_byte_swap`. Every edit
above is explained in more detail in the bullets earlier in this section.

## Touch calibration (frozen `indev.calibrate()` is unusable here)

The bundled `touch_calibrate.calibrate()` **must not** be used for this board. It forces the
display to rotation `_0` while sizing its targets from `indev._orig_width/_orig_height`,
which are the **landscape** dims (320x240) because the indev is created *after*
`set_rotation._90`. The portrait targets then land off-screen and the fitted affine is wrong.

Instead, calibrate in the current landscape rotation and save the affine to NVS. The test
helper `tests/board.py` does this in `board.calibrate_touch()`:

- shows a red square at 4 corners + centre (in 320x240 landscape),
- reads raw points via `indev._get_coords()` (already normalised to `_orig_width/_orig_height`),
- fits `A*raw + d` and writes `indev._cal` (`alphaX/betaX/deltaX`, `alphaY/betaY/deltaY`,
  `mirrorX/Y = False`), then `cal.save()`.

**The affine must target the pre-rotation coordinate, not the screen coordinate.**
LVGL rotates pointer points a second time in `indev_pointer_proc`
(`lib/lvgl/src/indev/lv_indev.c:693-701`) based on `disp->rotation`. Fitting
`raw -> screen` directly makes every touch land ~80px off (for rotation `_90`).
`_lvgl_rotation_inverse()` in `tests/board.py` computes the required target.

Two measurements worth remembering about that transform:

- it subtracts the **internal** `disp->ver_res`, which is the *unrotated* height
  (portrait **320**), **not** the 240 reported by `lv_display_get_vertical_resolution()`
  (the public API swaps for 90/270). So the `_90` inverse is `(ty, 319 - tx)` -
  using `239 - tx` is exactly the 80px error above.
- to derive any mapping on hardware, set an identity affine
  (`alphaX=1, betaX=0, deltaX=0, alphaY=0, betaY=1, deltaY=0`, in RAM only, do not
  `save()`), then `get_point()` returns the raw transform directly.

Result on hardware after the fix: `get_point` within ~6px of the actual tap at all four
corners + centre; `test_touch.py` dot and `test_lvgl.py` button/slider verified accurate.

## Build (recommended)

```bash
cd /Users/tony/Documents/VScode/AI_base/ESP32CYD_MPY/lvgl_micropython
python3 make.py esp32 --toml display_configs/CYD-2432S028R.toml --ccache --no-scrub
```

- First build takes ~15-30 min (toolchain download + ~2400 compile targets, twice if the
  partition needs auto-resizing). Rebuilds with ccache are much faster.
- `--no-scrub` keeps the build tree between runs (fast iteration). Drop it for a clean build.
- The process is long; if running under a tool with a short timeout, run it in the
  background and poll the log, e.g.:
  ```bash
  nohup python3 make.py esp32 --toml display_configs/CYD-2432S028R.toml --ccache --no-scrub \
    > /tmp/cyd_build.log 2>&1 &
  ```

### Explicit-driver build (no TOML)

Only for quick experiments; it does **not** encode the full CYD bus/pin topology, so the
display/touch wiring will not match. Prefer the TOML build.

```bash
python3 make.py esp32 BOARD=ESP32_GENERIC --flash-size=4 DISPLAY=ili9341 INDEV=xpt2046 --ccache --no-scrub
```

## Build output

Confirmed result (single merged image, flashed at offset `0x0`):

- `build/lvgl_micropy_ESP32_GENERIC-4.bin` (~2.9 MB)

Intermediate artifacts (in case you need them individually) are under
`lib/micropython/ports/esp32/build-ESP32_GENERIC/`:
`bootloader/bootloader.bin`, `partition_table/partition-table.bin`, `micropython.bin`.

The builder merges bootloader + partition table + app into the single `build/*.bin`.

## Flashing

The exact command is printed by the builder at the end of a successful build. Confirmed
command (replace `(PORT)`):

```bash
/Users/tony/.espressif/python_env/idf5.5_py3.13_env/bin/python -m esptool \
  --chip esp32 -p (PORT) -b 460800 --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m --erase-all \
  0x0 /Users/tony/Documents/VScode/AI_base/ESP32CYD_MPY/lvgl_micropython/build/lvgl_micropy_ESP32_GENERIC-4.bin
```

- The **merged bin flashes at `0x0`** (it already contains the bootloader which lives at 0x1000).
- Find the port on macOS: `ls /dev/cu.*`. The CYD typically shows up as
  `/dev/cu.usbserial-*`, `/dev/cu.wchusbserial*`, or `/dev/cu.SLAB_USBtoUART`.
- Or let the builder deploy: `python3 make.py esp32 --toml display_configs/CYD-2432S028R.toml deploy PORT=/dev/cu.usbserial-0001 BAUD=921600`.

## Verification

- Build log ends with `Project build complete.` and the esptool command.
- `build/lvgl_micropy_ESP32_GENERIC-4.bin` exists (note: `GENERIC` is uppercase).
- After flashing, open a serial REPL at `115200` (the `uart_repl_bitrate` in the TOML):
  `python -m serial.tools.miniterm /dev/cu.usbserial-0001 115200` (Ctrl-] to exit).

## Notes & gotchas

- **PSRAM:** classic CYD has none. Keep `BOARD_VARIANT=SPIRAM` off. The SPIRAM image still
  boots (MicroPython sets `CONFIG_SPIRAM_IGNORE_NOTFOUND=y`) but wastes RAM/heap layout.
- **Size (important):** the app partition is ~99.9% full (~3.9 KB free) on this build.
  The app partition auto-resizes: the first ESP-IDF pass reports
  "app partition is too small for binary micropython.bin" and triggers a second pass with a
  larger partition - this is normal and expected, not an error. If you add features,
  enable `optimize_size = true` (TOML) or `--optimize-size`, or drop drivers/modules.
- **`backlight_on_state`:** must be the driver that actually matches `[ILI9341.display]`.
  Using `st7789.STATE_PWM` pulls in an unused driver.
- **Orientation (verified the hard way):** the ILI9341 is portrait-native (240x320). For
  upright landscape 320x240 the panel needs MADCTL `MV` only (`0x20`), i.e. table index 1 =
  `32`. Upstream ships `96`/`160` (`MX|MV` / `MY|MV`) which are mirrored/180-flipped, and
  pairs them with `display_width/height = 320/240` (also wrong). Symptoms of the stock
  config: image not filling the panel (black band) and/or mirrored. Validate any change with
  `tests/test_pattern.py` (full-screen border + corner colours TL=white TR=red BL=green
  BR=blue). The CYD panel is **BGR** (`color_byte_order = "ili9341.BYTE_ORDER_BGR"` in the
  TOML); with the default RGB the image is upright but red/blue are swapped. To probe MADCTL
  live without rebuilding: `display.display.set_params(0x36, bytearray([0x28]))`
  (`0x20` landscape | `0x08` BGR).
- **Submodules:** `lib/*` (esp-idf, lvgl, micropython, pycparser) are cloned automatically
  by the builder. Do **not** run `git submodule update --init` manually.
- **Python 3.13:** the host python drives `make.py`; ESP-IDF uses its own venv. Only if the
  toolchain install fails should you switch to Homebrew Python 3.11.
- **ccache:** enabled in the TOML and via `--ccache`; keep `--no-scrub` for iteration.

## Repo layout (workspace root: `ESP32CYD_MPY/`)

- `lvgl_micropython/` - this build system (upstream `lvgl-micropython/lvgl_micropython`, branch `main`).
- `ESP32-Cheap-Yellow-Display/` - CYD docs/pinout reference (`PINS.md`, `cyd.md`, `DisplayConfig/User_Setup.h`).
