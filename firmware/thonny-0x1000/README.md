# ESP32 CYD Firmware — Thonny (flash @ 0x1000)

This image is **strip-prepared** for tools that flash at offset **`0x1000`** (like Thonny's built-in ESP32 firmware flasher).

The first `0x1000` bytes (4 KB) have been removed from the original merged image. When flashed at `0x1000`, the layout is correct: bootloader → flash `0x1000`, partition table → `0x8000`, application → `0x10000`.

## Flash with Thonny

1. Open Thonny → Tools → Manage Packages / or use "Install MicroPython" on ESP32? Alternatively: **Tools → Options → Interpreter** (or "Install MicroPython firmware")
2. Choose **Local file** and select `ESP32-CYD-2432S028R-lvgl-micropython-thonny.bin`
3. Select the correct serial port, and flash (Thonny writes at `0x1000` for ESP32)

If Thonny still shows `invalid header`/boot loops, try a full erase first, then flash again.

## Details

- Board: ESP32-2432S028R (ESP32-WROOM-32, 4MB flash, no PSRAM)
- MicroPython 1.27.0, LVGL 9.4.0, ESP-IDF 5.5.1
- Display: ILI9341 240x320 (driven 320x240 @ rotation _90, BGR)
- Touch: XPT2046
- Size: 2,932,944 bytes (stripped 4 KB from the 0x0 merged image)
- SHA256: `26fb7d8d88cac1c1171824dd0c16091f1db308eb9915ddeb3fe77cb6421652c9`
