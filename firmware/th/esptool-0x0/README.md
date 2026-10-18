# ESP32 CYD Firmware — English + Thai, esptool (flash @ 0x0)

This image adds **TinyTTF** (`LV_USE_TINY_TTF`) so Thai text can be rendered. It is the
**merged image** built to flash at offset **`0x0`** (bootloader at file offset `0x1000`,
partition table `0x8000`, application `0x10000`).

## Flash (recommended)

```bash
python -m esptool --chip esp32 -p PORT -b 460800 \
  --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m --erase-all \
  0x0 ESP32-CYD-2432S028R-lvgl-micropython-th.bin
```

- Replace `PORT` with your serial port (`/dev/cu.usbserial-*` on macOS).
- `--erase-all` erases the entire flash. It also wipes the data (filesystem) partition, so
  the font/shaper below must be copied again afterwards.

## Thai: copy the font + shaper to the board

The firmware includes TinyTTF, but the font and the Thai shaper are **not** frozen into the
image (the app partition is nearly full). Copy them once over the serial REPL:

```bash
mpremote connect PORT fs cp tests/fonts/Sarabun-Regular.ttf :Sarabun-Regular.ttf
mpremote connect PORT fs cp tests/thai.py :thai.py
```

Then, in your script:

```python
import lvgl as lv
import fs_driver
import thai

fs_driver.fs_register(lv.fs_drv_t(), "A")   # 'A:' -> board filesystem
tf = thai.ThaiFont("A:/Sarabun-Regular.ttf", 14)   # any pixel size
thai.render(lv.screen_active(), tf, "สวัสดี", 10, 10, lv.color_hex(0xFFFFFF))
```

See `../../../tests/README.md` for the shaper details and test scripts.

## Details

- Board: ESP32-2432S028R (ESP32-WROOM-32, 4MB flash, no PSRAM)
- MicroPython 1.27.0, LVGL 9.4.0 (TinyTTF enabled), ESP-IDF 5.5.1
- Display: ILI9341 240x320 (driven 320x240 @ rotation _90, BGR)
- Orientation: all four rotations upright (`_ORIENTATION_TABLE = [64, 32, 128, 224]`)
- Touch: XPT2046
- Size: 3,003,792 bytes
- SHA256: `6ad279a5dbf6e76d31eec770caa0d5742a2f46be754b4b07a8af0511f147182f`
