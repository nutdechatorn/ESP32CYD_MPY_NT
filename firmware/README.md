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

- `esptool-0x0/ESP32-CYD-2432S028R-lvgl-micropython.bin`: `bd312557ffaac8f41659558fa040cf9dc72f6cc5d5acae739c1c8e67de7b190b`
- `thonny-0x1000/ESP32-CYD-2432S028R-lvgl-micropython-thonny.bin`: `26fb7d8d88cac1c1171824dd0c16091f1db308eb9915ddeb3fe77cb6421652c9`
