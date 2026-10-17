# ESP32 Cheap Yellow Display (ESP32-2432S028R) Firmware

Prebuilt **MicroPython + LVGL** firmware for the classic ESP32 CYD (ESP32-2432S028R). Choose the image appropriate for your flashing tool.

## Available images

| Folder | Flash offset | Intended for | Notes |
|---|---|---|---|
| [`esptool-0x0/`](./esptool-0x0/) | `0x0` | `esptool` (CLI) | Original merged image (recommended). Bootloader/parttable/app correctly placed when flashed at `0x0`. |
| [`thonny-0x1000/`](./thonny-0x1000/) | `0x1000` | **Thonny** (ESP32 flasher) | First 0x1000 bytes stripped so Thonny's `0x1000` write lands bootloader/parttable/app at the correct flash addresses. |

## Usage manual

Full API reference with examples for every function:

- English: [`../docs/manual.en.md`](../docs/manual.en.md)
- Thai (ไทย): [`../docs/manual.th.md`](../docs/manual.th.md)

## Quick notes

- Port on macOS: usually `/dev/cu.usbserial-*` or `/dev/cu.wchusbserial*`
- `--erase-all` wipes the whole flash (including saved touch calibration). After flashing, you may need to recalibrate with `tests/board.py:calibrate_touch()`.
- The application partition is nearly full (~3.9 KB free).
- To build this image yourself, see `../lvgl_micropython/AGENTS.md`.

## SHA256 (for reference)

- `esptool-0x0/ESP32-CYD-2432S028R-lvgl-micropython.bin`: `77c4eed219721e6f1cdbd0b82808732c734ede07f680f06f4de1d89f555c6847`
- `thonny-0x1000/ESP32-CYD-2432S028R-lvgl-micropython-thonny.bin`: `d90f993748524c480a7db7bded3cfae2a7fd5cf2cbeca50805bc60332d8e6556`
