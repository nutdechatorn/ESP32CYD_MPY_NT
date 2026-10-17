# ESP32 Cheap Yellow Display (ESP32-2432S028R) Firmware

Prebuilt **MicroPython + LVGL** firmware for the classic ESP32 CYD
(ESP32-2432S028R). This is a single merged image: flash it and you get a Python
REPL with LVGL and a working display + touch.

| | |
| --- | --- |
| Board | ESP32-2432S028R (ESP32-WROOM-32, 4 MB flash, **no PSRAM**) |
| Display | ILI9341 240x320 panel, driven as landscape 320x240 (`set_rotation._90`, BGR) |
| Touch | XPT2046 (resistive) |
| MicroPython | 1.27.0 |
| LVGL | 9.4.0 |
| ESP-IDF | 5.5.1 |
| File | `ESP32-CYD-2432S028R-lvgl-micropython.bin` (merged, 2,937,040 bytes) |
| SHA256 | `bd312557ffaac8f41659558fa040cf9dc72f6cc5d5acae739c1c8e67de7b190b` |

## Flash

Flash the merged image at offset **`0x0`**. You need
[esptool](https://github.com/espressif/esptool) (`pip install esptool`).

macOS / Linux:

```bash
python -m esptool --chip esp32 -p /dev/ttyUSB0 -b 460800 \
  --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m --erase-all \
  0x0 ESP32-CYD-2432S028R-lvgl-micropython.bin
```

Windows: use `-p COMx` (check Device Manager for the port). On macOS the port is
usually `/dev/cu.usbserial-*` or `/dev/cu.wchusbserial*`.

After flashing, open the REPL at **115200** baud (e.g. `mpremote connect <port>`).

## Usage manual

Full API reference with examples for every function:

- English: [`../docs/manual.en.md`](../docs/manual.en.md)
- Thai (ไทย): [`../docs/manual.th.md`](../docs/manual.th.md)

## Notes

- `--erase-all` wipes the whole flash, including the touch calibration stored in
  NVS. Re-calibrate with the test helper (`tests/board.py:calibrate_touch()`).
- The application partition is nearly full (about 3.9 KB free).
- To build this image yourself, see `lvgl_micropython/AGENTS.md`.
