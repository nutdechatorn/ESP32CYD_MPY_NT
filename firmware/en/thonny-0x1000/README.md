# ESP32 CYD Firmware — English only, Thonny (flash @ 0x1000)

English-only build (TinyTTF disabled), **strip-prepared** for tools that flash at offset
**`0x1000`** (like Thonny's built-in ESP32 firmware flasher).

The first `0x1000` bytes (4 KB) have been removed from the merged image. When flashed at
`0x1000`, the layout is correct: bootloader → flash `0x1000`, partition table → `0x8000`,
application → `0x10000`.

## Flash with Thonny

1. Open Thonny → **Tools → Options → Interpreter** (or "Install MicroPython firmware")
2. Choose **Local file** and select `ESP32-CYD-2432S028R-lvgl-micropython-en-thonny.bin`
3. Select the correct serial port and flash (Thonny writes at `0x1000` for ESP32)

If Thonny still shows `invalid header`/boot loops, erase first, then flash again.

## Details

- Board: ESP32-2432S028R (ESP32-WROOM-32, 4MB flash, no PSRAM)
- MicroPython 1.27.0, LVGL 9.4.0, ESP-IDF 5.5.1
- Display: ILI9341 240x320 (driven 320x240 @ rotation _90, BGR)
- Orientation: all four rotations upright (`_ORIENTATION_TABLE = [64, 32, 128, 224]`)
- Touch: XPT2046
- **No Thai support** (no TinyTTF). For Thai, use `../../th/thonny-0x1000/`.
- Size: 2,932,944 bytes (stripped 4 KB from the 0x0 merged image)
- SHA256: `d90f993748524c480a7db7bded3cfae2a7fd5cf2cbeca50805bc60332d8e6556`
