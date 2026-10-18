# ESP32 Cheap Yellow Display (ESP32-2432S028R) Firmware

Prebuilt **MicroPython + LVGL** firmware for the classic ESP32 CYD (ESP32-2432S028R).
Two language variants are provided, and each variant comes in two flash-tool flavours.

## Available images

| Variant | Folder | Notes |
|---|---|---|
| **English only** | [`en/`](./en/) | Smallest image. No TinyTTF, no Thai shaping. |
| **English + Thai** | [`th/`](./th/) | Adds TinyTTF so Thai (and any TTF) text can be rendered. ~65 KB larger. |

Each variant folder contains two images, one per flashing tool:

| Folder | Flash offset | Intended for |
|---|---|---|
| `esptool-0x0/` | `0x0` | `esptool` (CLI) — merged image (recommended). |
| `thonny-0x1000/` | `0x1000` | **Thonny** (ESP32 firmware flasher) — first 4 KB stripped. |

Filenames:

| Language | esptool @ `0x0` | Thonny @ `0x1000` |
|---|---|---|
| English only | `en/esptool-0x0/ESP32-CYD-2432S028R-lvgl-micropython-en.bin` | `en/thonny-0x1000/ESP32-CYD-2432S028R-lvgl-micropython-en-thonny.bin` |
| English + Thai | `th/esptool-0x0/ESP32-CYD-2432S028R-lvgl-micropython-th.bin` | `th/thonny-0x1000/ESP32-CYD-2432S028R-lvgl-micropython-th-thonny.bin` |

## Which one do I want?

- Use **`en/`** if you only need Latin/ASCII UI text.
- Use **`th/`** if you need Thai text. This firmware includes TinyTTF, but the font and the
  shaper live on the board filesystem (the app partition is nearly full, so they cannot be
  frozen). After flashing, copy them once:

  ```bash
  mpremote connect PORT fs cp tests/fonts/Sarabun-Regular.ttf :Sarabun-Regular.ttf
  mpremote connect PORT fs cp tests/thai.py :thai.py
  ```

  Then render Thai with `thai.render(...)`; see `../docs/manual.*.md` and `../tests/README.md`.

## SHA256 (for reference)

- `en/...-en.bin`: `77c4eed219721e6f1cdbd0b82808732c734ede07f680f06f4de1d89f555c6847`
- `en/...-en-thonny.bin`: `d90f993748524c480a7db7bded3cfae2a7fd5cf2cbeca50805bc60332d8e6556`
- `th/...-th.bin`: `6ad279a5dbf6e76d31eec770caa0d5742a2f46be754b4b07a8af0511f147182f`
- `th/...-th-thonny.bin`: `d29d2a2bd605eb88cfca0b040102151d6a2fc6e8ce5ad6b046a0dc857e2596c7`

## Usage manual

Full API reference with examples for every function:

- English: [`../docs/manual.en.md`](../docs/manual.en.md)
- Thai (ไทย): [`../docs/manual.th.md`](../docs/manual.th.md)

## Quick notes

- Port on macOS: usually `/dev/cu.usbserial-*` or `/dev/cu.wchusbserial*`
- `--erase-all` wipes the whole flash (including saved touch calibration and any files you
  copied to the filesystem). After flashing, you may need to recalibrate with
  `tests/board.py:calibrate_touch()` and re-copy the Thai font/shaper.
- The application partition is nearly full (~3.9 KB free on `en`, ~2.7 KB on `th`).
- To build these images yourself, see `../lvgl_micropython/AGENTS.md` and run
  `./build.sh en` / `./build.sh th`.
