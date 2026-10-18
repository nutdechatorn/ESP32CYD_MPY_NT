# ESP32 CYD Firmware — English + Thai, Thonny (flash @ 0x1000)

This image adds **TinyTTF** so Thai text can be rendered. It is **strip-prepared** for tools
that flash at offset **`0x1000`** (like Thonny's built-in ESP32 firmware flasher).

The first `0x1000` bytes (4 KB) have been removed from the merged image. When flashed at
`0x1000`, the layout is correct: bootloader → flash `0x1000`, partition table → `0x8000`,
application → `0x10000`.

## Flash with Thonny

1. Open Thonny → **Tools → Options → Interpreter** (or "Install MicroPython firmware")
2. Choose **Local file** and select `ESP32-CYD-2432S028R-lvgl-micropython-th-thonny.bin`
3. Select the correct serial port and flash (Thonny writes at `0x1000` for ESP32)

If Thonny still shows `invalid header`/boot loops, erase first, then flash again.

## Thai: copy the font + shaper to the board

The firmware includes TinyTTF, but the font and shaper live on the board filesystem (they do
not fit in the app partition). Copy them once:

```bash
mpremote connect PORT fs cp tests/fonts/Sarabun-Regular.ttf :Sarabun-Regular.ttf
mpremote connect PORT fs cp tests/thai.py :thai.py
```

See `../../../tests/README.md` and the manual for usage.

## Details

- Board: ESP32-2432S028R (ESP32-WROOM-32, 4MB flash, no PSRAM)
- MicroPython 1.27.0, LVGL 9.4.0 (TinyTTF enabled), ESP-IDF 5.5.1
- Display: ILI9341 240x320 (driven 320x240 @ rotation _90, BGR)
- Orientation: all four rotations upright (`_ORIENTATION_TABLE = [64, 32, 128, 224]`)
- Touch: XPT2046
- Size: 2,999,696 bytes (stripped 4 KB from the 0x0 merged image)
- SHA256: `d29d2a2bd605eb88cfca0b040102151d6a2fc6e8ce5ad6b046a0dc857e2596c7`
