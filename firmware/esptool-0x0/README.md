# ESP32 CYD Firmware — esptool (flash @ 0x0)

This is the **merged image** built to flash at offset **`0x0`**. It contains the bootloader (at file offset `0x1000`), partition table (`0x8000`) and application (`0x10000`).

## Flash (recommended)

```bash
python -m esptool --chip esp32 -p PORT -b 460800 \
  --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m --erase-all \
  0x0 ESP32-CYD-2432S028R-lvgl-micropython.bin
```

- Replace `PORT` with your serial port (`/dev/cu.usbserial-*` on macOS).
- `--erase-all` erases the entire flash (including saved touch calibration).

## Details

- Board: ESP32-2432S028R (ESP32-WROOM-32, 4MB flash, no PSRAM)
- MicroPython 1.27.0, LVGL 9.4.0, ESP-IDF 5.5.1
- Display: ILI9341 240x320 (driven 320x240 @ rotation _90, BGR)
- Touch: XPT2046
- Size: 2,937,040 bytes
- SHA256: `bd312557ffaac8f41659558fa040cf9dc72f6cc5d5acae739c1c8e67de7b190b`
