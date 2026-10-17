# ESP32 CYD — คู่มือการใช้งาน MicroPython + LVGL (ภาษาไทย)

> English: [`manual.en.md`](manual.en.md)

คู่มือฉบับสมบูรณ์สำหรับการใช้งานเฟิร์มแวร์ **MicroPython + LVGL** ที่ build ไว้แล้ว
บนบอร์ด **ESP32 Cheap Yellow Display (CYD) — รุ่น ESP32-2432S028R**

เนื้อหาครอบคลุมตัวบอร์ด, การแฟลช, การใช้ REPL, API ของจอและทัช, ไลบรารีกราฟิก LVGL,
ฟังก์ชันที่ใช้บ่อยทั้งหมด พร้อมตัวอย่างการใช้งานของแต่ละฟังก์ชัน ชื่อ API ทั้งหมด
ตรวจสอบเทียบกับซอร์สจริงของเฟิร์มแวร์แล้ว (`lvgl.pyi`, โมดูล `display`/`indev` ที่
freeze ไว้ และสคริปต์ใน `tests/`)

---

## สารบัญ

1. [สิ่งที่คุณได้มา](#1-สิ่งที่คุณได้มา)
2. [ข้อมูลบอร์ดและพิน](#2-ข้อมูลบอร์ดและพิน)
3. [เริ่มต้นอย่างรวดเร็ว](#3-เริ่มต้นอย่างรวดเร็ว)
4. [โมดูล `display` ที่ freeze ไว้](#4-โมดูล-display-ที่-freeze-ไว้)
5. [ตัวช่วย `board`](#5-ตัวช่วย-board)
6. [API จอแสดงผล — `ili9341`](#6-api-จอแสดงผล--ili9341)
7. [API ทัช — `xpt2046`](#7-api-ทัช--xpt2046)
8. [พื้นฐาน LVGL](#8-พื้นฐาน-lvgl)
9. [วิดเจ็ต LVGL](#9-วิดเจ็ต-lvgl)
10. [อีเวนต์ (Events)](#10-อีเวนต์-events)
11. [สไตล์ (Styles)](#11-สไตล์-styles)
12. [โมดูลระบบ](#12-โมดูลระบบ)
13. [โปรแกรมตัวอย่างแบบเต็ม](#13-โปรแกรมตัวอย่างแบบเต็ม)
14. [จุดสังเกต/ข้อควรระวังของ binding](#14-จุดสังเกตข้อควรระวังของ-binding)
15. [การแก้ปัญหา](#15-การแก้ปัญหา)
16. [ชุดทดสอบ](#16-ชุดทดสอบ)
17. [การ build เฟิร์มแวร์ใหม่](#17-การ-build-เฟิร์มแวร์ใหม่)

---

## 1. สิ่งที่คุณได้มา

ไฟล์เฟิร์มแวร์ `firmware/ESP32-CYD-2432S028R-lvgl-micropython.bin` เป็นภาพรวม
(merged image) ไฟล์เดียว ประกอบด้วย:

| องค์ประกอบ | เวอร์ชัน |
| --- | --- |
| MicroPython | 1.27.0 |
| LVGL | 9.4.0 |
| ESP-IDF | 5.5.1 |
| บอร์ด | ESP32-2432S028R (ESP32-WROOM-32, flash 4 MB, **ไม่มี PSRAM**) |

หลังแฟลชแล้ว คุณจะได้ REPL ของ Python ผ่านพอร์ตอนุกรม โดยมีไลบรารีกราฟิก (`lvgl`),
ไดรเวอร์จอ (`ili9341`), ไดรเวอร์ทัช (`xpt2046`) และจอ+ทัชถูกเริ่มต้นให้แล้วโดยโมดูล
`display` ที่ freeze ไว้

**พาร์ทิชันแอปเกือบเต็ม** (เหลือว่างประมาณ 3.9 KB) จึงเพิ่มขนาดได้อีกไม่มาก
ถ้าไม่เปิด `optimize_size` แล้ว build ใหม่ สคริปต์ MicroPython ที่คุณเขียนจะอยู่บน
ไฟล์ซิสเต็ม FAT ขนาดเล็ก ไม่ได้อยู่ในพาร์ทิชันแอป จึงไม่มีปัญหาเรื่องนี้

---

## 2. ข้อมูลบอร์ดและพิน

| หน้าที่ | สัญญาณ | GPIO |
| --- | --- | --- |
| จอ (ILI9341, SPI host 1) | MOSI | 13 |
| | MISO | 12 |
| | SCK | 14 |
| | CS | 15 |
| | DC | 2 |
| | แบ็คไลต์ (PWM) | 21 |
| | Reset | ไม่ได้ต่อ |
| ทัช (XPT2046, SPI host 2) | MOSI | 32 |
| | MISO | 39 |
| | SCK | 25 |
| | CS | 33 |
| | IRQ | 36 |

- ความละเอียดจอ: **240x320 แนวตั้ง** (native) ขับเป็น **320x240 แนวนอน** ด้วย
  การหมุน `_90`
- ลำดับสีของแผง: **BGR** (จัดการในคอนฟิกแล้ว คุณไม่ต้องตั้งในโค้ด)
- พินควบคุมอื่น ๆ (เช่น LED RGB, ลำโพง) ไม่ได้เชื่อมในเฟิร์มแวร์นี้

---

## 3. เริ่มต้นอย่างรวดเร็ว

### 3.1 แฟลชเฟิร์มแวร์

ติดตั้ง esptool, หาพอร์ตอนุกรม แล้วแฟลช merged image ที่ offset `0x0`
`--erase-all` จะลบ flash ทั้งหมด (รวมการคาลิเบรตทัชที่บันทึกไว้)

```bash
pip install esptool

# macOS / Linux — ตัวอย่างพอร์ต /dev/cu.usbserial-0001
python -m esptool --chip esp32 -p /dev/cu.usbserial-0001 -b 460800 \
  --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m --erase-all \
  0x0 ESP32-CYD-2432S028R-lvgl-micropython.bin
```

Windows: เปลี่ยนพอร์ตเป็น `-p COM5` (ดูจาก Device Manager)

ดูรายชื่อพอร์ตบน macOS ด้วย `ls /dev/cu.*`; บอร์ด CYD มักขึ้นเป็น
`/dev/cu.usbserial-*`, `/dev/cu.wchusbserial*` หรือ `/dev/cu.SLAB_USBtoUART`

### 3.2 เปิด REPL

REPL ทำงานที่ **115200 baud**

```bash
pip install mpremote

mpremote connect /dev/cu.usbserial-0001 repl     # พร้อมท์แบบโต้ตอบ (กด Ctrl-] เพื่อออก)
```

`mpremote` ใช้ `connect <port>`; ไม่รับออปชัน `--port`

### 3.3 รันสคริปต์แรกของคุณ

สร้างไฟล์ `hello.py`:

```python
import lvgl as lv
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x003060), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

label = lv.label(scr)
label.set_text('Hello CYD!')
label.center()
scr.invalidate()
```

รันด้วย:

```bash
mpremote connect /dev/cu.usbserial-0001 run hello.py
```

> **สำคัญ:** `mpremote run` จะจบทันทีเมื่อโค้ดระดับบนสุดของสคริปต์ทำงานเสร็จ
> ถ้าต้องการให้ยังตอบสนองต่อ (ทัช, แอนิเมชัน LVGL) ต้องปิดท้ายสคริปต์ด้วยลูป
> — ดู [§8.9](#89-ลูปหลัก-main-loop)

---

## 4. โมดูล `display` ที่ freeze ไว้

`import display` จะเริ่มต้นบอร์ดทั้งบอร์ดให้ โมดูลนี้ถูกสร้างจากคอนฟิกการ build
`display_configs/CYD-2432S028R.toml` โค้ด Python ที่ทำงานจริงเทียบเท่าดังนี้:

```python
import machine, lcd_bus, ili9341, lvgl as lv, xpt2046, task_handler

spi_bus = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2_000_000, cs=33)

display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=24_000_000, dc=2, cs=15)

display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=240,
    display_height=320,
    backlight_pin=21,
    backlight_on_state=ili9341.STATE_PWM,
    color_byte_order=ili9341.BYTE_ORDER_BGR,   # แผง CYD เป็น BGR
    color_space=lv.COLOR_FORMAT.RGB565,
    rgb565_byte_swap=True,
)
display._ORIENTATION_TABLE = [64, 32, 128, 224]  # ทั้ง 4 rotation หงายถูก (ดูหมายเหตุ)
display.set_power(True)
display.init(1)
display.set_rotation(lv.DISPLAY_ROTATION._90)   # แนวนอน 320x240
display.set_backlight(100)

indev = xpt2046.XPT2046(device=indev_device)

task_handler.TaskHandler()                       # ปั๊ม timer + flush ของ LVGL
```

> `_ORIENTATION_TABLE` เก็บไบต์ MADCTL ของ ILI9341 หนึ่งค่าต่อหนึ่ง rotation
> (บิต BGR `0x08` จะถูก OR เข้าไปตอนรันไทม์) ที่นี่ใช้ `[0x40, 0x20, 0x80, 0xE0]`:
> บิต `MV` (`0x20`) บอกโหมดแนวนอน (`_90` / `_270`) และ rotation ที่ห่างกัน 180°
> จะต่างกันที่ XOR `0xC0` ค่าเริ่มต้น `[0, 96, 192, 160]` ทำให้ภาพ **กลับด้าน**;
> ค่าเก่า `[0, 32, 192, 160]` ทำให้ `_0` และ `_270` กลับด้าน แก้เฉพาะเมื่อเปลี่ยนจอ

หลัง `import display` คุณจะได้ออบเจ็กต์ที่มีประโยชน์ 2 ตัว:

| ชื่อ | ชนิด | คืออะไร |
| --- | --- | --- |
| `display.display` | `ili9341.ILI9341` | ไดรเวอร์จอ (ตัวห่อ `display_t` ของ LVGL) |
| `display.indev` | `xpt2046.XPT2046` | ไดรเวอร์ทัช (ตัวห่อ `indev_t` ของ LVGL) |

จอถูกตั้งเป็นจอเริ่มต้นของ LVGL และ `TaskHandler` จะเริ่มตัวจับเวลา tick/flush ของ
LVGL ไว้เบื้องหลัง

> `import display` ใช้ได้ครั้งเดียวต่อการจ่ายไฟหนึ่งรอบ การ soft reset ของ
> MicroPython จะ **ไม่** คืน ESP32 SPI host ดังนั้น `import display` ครั้งที่สองใน
> รอบไฟเดียวกันจะล้มด้วย `TypeError: can't convert str to int` ตอนสร้าง SPI bus ใหม่
> ต้อง **hard reset** (ดู [§16](#16-ชุดทดสอบ)) ระหว่างการรันแต่ละครั้ง

---

## 5. ตัวช่วย `board`

`tests/board.py` เป็นตัวห่ออำนวยความสะดวก (สคริปต์ของคุณก็คัดลอกฟังก์ชันเหล่านี้ได้)
การ import มันจะทำ `import display` ให้ด้วย

```python
import board
```

| ฟังก์ชัน | คืนค่า | คำอธิบาย |
| --- | --- | --- |
| `board.lcd` | `ili9341.ILI9341` | ไดรเวอร์จอ |
| `board.touch` | `xpt2046.XPT2046` | ไดรเวอร์ทัช |
| `board.width()` | int | ความกว้างจอ (320, แนวนอน) |
| `board.height()` | int | ความสูงจอ (240, แนวนอน) |
| `board.size()` | `(w, h)` | ความกว้างและความสูงพร้อมกัน |
| `board.backlight(level)` | – | ตั้งความสว่างแบ็คไลต์ `0`–`100` (%) |
| `board.calibrate_touch(force=False)` | bool | คาลิเบรตทัชแบบ 5 จุด (ต้องแตะจริง) |
| `board.reset_touch_cal()` | – | ลบการคาลิเบรตทัชที่บันทึกไว้ |
| `board.dump_info()` | – | พิมพ์รายงานเฟิร์มแวร์/บอร์ด |

ตัวอย่าง:

```python
import board
print(board.size())          # (320, 240)
board.backlight(50)          # หรี่ลง 50%
board.dump_info()
```

---

## 6. API จอแสดงผล — `ili9341`

คลาสคือ `ili9341.ILI9341` (สืบทอดจาก `DisplayDriver`) ค่าคงที่ระดับโมดูล:

| ค่าคงที่ | ค่า | ความหมาย |
| --- | --- | --- |
| `ili9341.STATE_HIGH` | 1 | ขา active สูง |
| `ili9341.STATE_LOW` | 0 | ขา active ต่ำ |
| `ili9341.STATE_PWM` | -1 | เอาต์พุต PWM (ใช้กับแบ็คไลต์) |
| `ili9341.BYTE_ORDER_RGB` | 0x00 | ลำดับสี RGB (ค่าเริ่มต้น) |
| `ili9341.BYTE_ORDER_BGR` | 0x08 | ลำดับสี BGR (แผงนี้) |

### 6.1 แบ็คไลต์

```python
lcd = board.lcd
lcd.set_backlight(100)     # 0..100 (%)
lcd.set_backlight(0)       # ปิด
print(lcd.get_backlight()) # 100.0
```

### 6.2 เปิด/ปิดกำลัง และรีเซ็ต

```python
lcd.set_power(True)
print(lcd.get_power())
lcd.reset()                # ใช้เมื่อมีขา reset (บน CYD ไม่มี)
```

### 6.3 ความละเอียดและการหมุน

```python
print(lcd.get_horizontal_resolution())  # 320
print(lcd.get_vertical_resolution())    # 240
print(lcd.get_rotation())               # lv.DISPLAY_ROTATION._90
lcd.set_rotation(lv.DISPLAY_ROTATION._0)    # กลับเป็นแนวตั้ง 240x320
lcd.set_rotation(lv.DISPLAY_ROTATION._90)   # แนวนอน 320x240 (ค่าเริ่มต้น)
```

ค่าการหมุน: `lv.DISPLAY_ROTATION._0`, `._90`, `._180`, `._270`

### 6.4 สั่งคอนโทรลเลอร์ตรง ๆ (ขั้นสูง)

`set_params` / `get_params` คุยกับไอซี ILI9341 โดยตรง เช่น ตั้งค่า MADCTL
สำหรับแนวนอน + BGR (ไบต์ `0x28`):

```python
lcd.set_params(0x36, bytearray([0x28]))   # 0x20 (MV) | 0x08 (BGR)
```

### 6.5 รูปแบบสี และการกลับสี

```python
lcd.set_color_format(lv.COLOR_FORMAT.RGB565)
print(lcd.get_color_format())
lcd.set_color_inversion(False)  # พลิกถ้าดำ/ขาวกลับด้าน
```

### 6.6 เมธอดที่มีประโยชน์อื่น ๆ

| เมธอด | คำอธิบาย |
| --- | --- |
| `set_physical_resolution(w, h)` | ตั้งความละเอียดกายภาพของแผง |
| `set_offset(x, y)` / `get_offset_x()` / `get_offset_y()` | ออฟเซตการวาด |
| `set_dpi(dpi)` / `get_dpi()` | ความหนาแน่น (มีผลกับขนาดวิดเจ็ต) |
| `is_double_buffered()` | ใช้บัฟเฟอร์วาดคู่หรือไม่ |
| `get_screen_active()` / `get_layer_top()` / `get_layer_sys()` / `get_layer_bottom()` | ออบเจ็กต์หน้า/เลเยอร์ของ LVGL |
| `set_theme(theme)` / `get_theme()` | ธีม LVGL |
| `set_default()` | ตั้งเป็นจอเริ่มต้น |
| `add_event_cb(cb, filter, user_data)` | ฟังอีเวนต์ของจอ |
| `init(type=None)` | (รันใหม่) ลำดับ init ของแผง |
| `del lcd` | ลบอินสแตนซ์ (วิธีเดียวที่รองรับ — `lcd.delete()` จะ raise) |

---

## 7. API ทัช — `xpt2046`

คลาสคือ `xpt2046.XPT2046` (สืบทอดจาก `PointerDriver`) เป็นอุปกรณ์อินพุตพอยน์เตอร์
ของ LVGL

แอตทริบิวต์ระดับคลาสที่ปรับได้ก่อนสร้างอินสแตนซ์:
`touch_threshold = 400`, `confidence = 5`, `margin = 50`

### 7.1 การอ่านตำแหน่งทัช

วิธีที่เชื่อถือได้ที่สุดในการอ่านจุดปัจจุบัน (ใช้ได้ในอีเวนต์ callback ด้วย) คือ
`get_point` กับ `lv.point_t`:

```python
pt = lv.point_t()
board.touch.get_point(pt)
print(pt.x, pt.y)
```

`touch.get_point(pt)` จะเติม `pt.x` / `pt.y` เป็นพิกัด **บนจอ**

### 7.2 การคาลิเบรต

| สมาชิก | คำอธิบาย |
| --- | --- |
| `touch.is_calibrated` | `True` เมื่อมีการคาลิเบรตที่บันทึกไว้ |
| `touch.calibrate()` | **ใช้ไม่ได้บนบอร์ดนี้** (ดูด้านล่าง) |
| `board.calibrate_touch(force=False)` | คาลิเบรต 5 จุดแบบโต้ตอบ (ใช้ตัวนี้) |
| `board.reset_touch_cal()` | ลบการคาลิเบรตที่บันทึกไว้ |
| `touch._cal` | ออบเจ็กต์ `TouchCalData` (ขั้นสูง) |

ฟิลด์ของ `touch._cal` (`TouchCalData`) — สมการ affine 3x3 เก็บใน NVS:
`alphaX, betaX, deltaX, alphaY, betaY, deltaY, mirrorX, mirrorY` พร้อม `save()`
และ `reset()`

ตัวอย่าง — คาลิเบรตถ้าจำเป็น แล้วอ่านจุด:

```python
import lvgl as lv
import board

board.calibrate_touch()          # แสดงสี่เหลี่ยมแดง แตะทีละจุด
pt = lv.point_t()
board.touch.get_point(pt)
print('screen', pt.x, pt.y)
```

> **ทำไมไม่ใช้ `touch.calibrate()`?** ตัวคาลิเบรตที่ freeze ไว้บังคับจอเป็น
> การหมุน `_0` แต่คำนวณตำแหน่งเป้าหมายจากขนาด *แนวนอน* ทำให้เป้าหมายหลุดจอ
> `board.calibrate_touch()` ทำงานในการหมุนแนวนอนจริง และ fit สมการ affine ไปยัง
> พิกัดก่อนการหมุนที่ LVGL ต้องการ (LVGL หมุนพิกัดพอยน์เตอร์ซ้ำอีกครั้ง) ผลลัพธ์:
> แม่นยำประมาณ 6 px ที่ทุกมุมและตรงกลาง

### 7.3 เมธอดอื่นของพอยน์เตอร์

| เมธอด | คำอธิบาย |
| --- | --- |
| `touch.enable(en)` | เปิด/ปิดอุปกรณ์ |
| `touch.get_state()` | `lv.INDEV_STATE.PRESSED` / `.RELEASED` |
| `touch.get_width()` / `get_height()` | ขอบเขตที่อุปกรณ์รายงาน |
| `touch.get_rotation()` | การหมุนจอปัจจุบัน |
| `touch.get_point(pt)` | เติม `pt` ด้วยพิกัดบนจอ |
| `touch.get_vect(pt)` | เติม `pt` ด้วยเวกเตอร์การเคลื่อนที่ |
| `touch.get_scroll_obj()` / `get_scroll_dir()` / `get_gesture_dir()` | ข้อมูลท่าทาง |
| `touch.set_cursor(obj)` | ตั้งออบเจ็กต์เคอร์เซอร์ที่ตามพอยน์เตอร์ |
| `touch.reset_long_press()` | รีเซ็ตสถานะกดค้าง |
| `touch.read()` | บังคับอ่านค่า |
| `touch.search_obj(pt)` | hit-test กับ `lv.point_t` |
| `touch.add_event_cb(cb, filter, user_data)` | ฟังอีเวนต์ของ indev |
| `xpt2046.XPT2046.active()` | พอยน์เตอร์ที่ active หรือ `None` |

> ภายในอีเวนต์ callback ของ LVGL `lv.indev_active()` อาจคืน `None` ใน binding นี้
> — ให้อ่านจุดจากไดรเวอร์ (`board.touch.get_point(pt)`) แทน

---

## 8. พื้นฐาน LVGL

`import lvgl as lv` ไลบรารีถูกเริ่มต้นโดย `import display` ถ้าสร้างเองให้เรียก
`lv.init()`

### 8.1 หน้าจอ (Screens)

จอแต่ละจอมี "active screen" หน้าจอเป็นอินสแตนซ์ `lv.obj` ธรรมดา

```python
scr = lv.screen_active()      # หน้าจอปัจจุบัน
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

new = lv.obj()                # หน้าจอใหม่ (ไม่มี parent)
lv.screen_load(new)           # สลับไป (ทันที)
lv.screen_load_anim(new2, lv.SCREEN_LOAD_ANIM.MOVE_LEFT, 300, 0, True)
```

เลเยอร์อยู่เหนือ/ใต้หน้าจอ: `lv.layer_top()`, `lv.layer_sys()`, `lv.layer_bottom()`

### 8.2 การสร้างออบเจ็กต์

วิดเจ็ตสร้างโดยส่ง parent เป็นอาร์กิวเมนต์ตำแหน่งเดียว:

```python
btn  = lv.button(scr)
lbl  = lv.label(btn)
```

### 8.3 เรขาคณิต (ตำแหน่ง/ขนาด)

```python
obj.set_pos(x, y)
obj.set_size(w, h)
obj.align(lv.ALIGN.CENTER, 0, 0)          # จัดตำแหน่ง + ออฟเซต (x, y)
obj.align_to(other, lv.ALIGN.OUT_RIGHT_MID, 8, 0)
obj.center()                              # ทางลัดของการจัด CENTER
print(obj.get_width(), obj.get_height())
obj.set_x(10); obj.set_y(20)
obj.set_width(80); obj.set_height(40)
```

`lv.ALIGN.*`: `TOP_LEFT, TOP_MID, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_MID,
BOTTOM_RIGHT, LEFT_MID, RIGHT_MID, CENTER, OUT_TOP_LEFT … OUT_RIGHT_BOTTOM`

### 8.4 แฟล็กและสถานะ

```python
obj.add_flag(lv.obj.FLAG.HIDDEN)      # ซ่อน (ใช้ remove_flag เพื่อแสดง)
obj.remove_flag(lv.obj.FLAG.CLICKABLE)
obj.add_state(lv.STATE.DISABLED)
```

แฟล็กที่พบบ่อย: `HIDDEN`, `CLICKABLE`, `SCROLLABLE`, `CHECKABLE`, `PRESS_LOCK`,
`EVENT_BUBBLE`, `IGNORE_LAYOUT`
> binding นี้ **ไม่มี `clear_flag`** — ให้ใช้ `remove_flag`
> และใช้ `lv.obj.FLAG.*` (ไม่ใช่ `lv.OBJ_FLAG.*`)

### 8.5 สีและความทึบ

```python
lv.color_hex(0xFF0000)          # 0xRRGGBB -> สี
lv.color_make(255, 0, 0)        # จาก r, g, b
lv.color_white() / lv.color_black()
lv.palette_main(lv.PALETTE.BLUE)
lv.palette_lighten(lv.PALETTE.BLUE, 2)
lv.OPA.TRANSP / lv.OPA.COVER / lv.OPA._50
```

### 8.6 ข้อความ ฟอนต์ และสัญลักษณ์

```python
lbl.set_text('Hello')
lbl.set_style_text_font(lv.font_montserrat_16, 0)   # มี 12 / 14 / 16
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
```

มีฟอนต์ในตัวเฉพาะ `lv.font_montserrat_12`, `lv.font_montserrat_14`,
`lv.font_montserrat_16` (และ `lv.font_get_default()`) สัญลักษณ์เช่น
`lv.SYMBOL.OK`, `lv.SYMBOL.CLOSE`, `lv.SYMBOL.PLAY` ใช้ในข้อความ/ป้ายได้

### 8.7 การใส่สไตล์ (ดูเพิ่มที่ [§11](#11-สไตล์-styles))

```python
obj.set_style_bg_color(lv.color_hex(0x202020), 0)
obj.set_style_bg_opa(lv.OPA.COVER, 0)
obj.set_style_radius(8, 0)
obj.set_style_border_width(0, 0)
obj.set_style_pad_all(8, 0)
```

### 8.8 การวาดใหม่

LVGL วาดใหม่ให้อัตโนมัติภายใน task handler บังคับได้ด้วย:

```python
obj.invalidate()
scr.invalidate()
```

### 8.9 ลูปหลัก (Main loop)

`TaskHandler` ที่ freeze ไว้เรียก `lv.tick_inc()` + `lv.task_handler()` ตามตัวจับเวลา
อยู่แล้ว เมื่อรันเป็น **สคริปต์** (ไม่ใช่แอปที่ freeze) คุณต้องทำให้ interpreter ยัง
ทำงานอยู่ เพื่อให้ลูปนั้นได้ทำงาน — ไม่เช่นนั้น `mpremote run` จะจบและ UI จะค้าง
ท้ายสคริปต์ที่ใช้บ่อยคือ:

```python
import lcd_bus, time
while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
```

`lcd_bus._pump_main_thread()` จะดูแลจอ/DMA + LVGL จากเมนเธรด (หรือจะเรียก
`lv.timer_handler()` เองก็ได้)

### 8.10 ตัวจับเวลาและแอนิเมชัน

```python
def tick(t):
    print('tick')

timer = lv.timer_create(tick, 500, None)   # ทุก 500 ms
timer.set_repeat_count(-1)                 # ตลอดไป (-1) หรือจำนวนครั้ง
timer.delete()                             # หยุด

anim = lv.anim_t()
anim.set_var(slider)
anim.set_values(0, 100)
anim.set_duration(800)
anim.set_path_cb(lv.anim_t.path_ease_in_out)
anim.start()
```

---

## 9. วิดเจ็ต LVGL

`parent` เป็นอาร์กิวเมนต์แรก (ตำแหน่ง) เสมอ คอนสตรัคเตอร์ของ binding นี้ไม่รับ
อาร์กิวเมนต์อื่น ให้ตั้งค่าด้วยเมธอดหลังจากนั้น อาร์กิวเมนต์ของเมธอดเป็น
**positional-only**

### 9.1 `lv.obj` — ออบเจ็กต์ฐาน / คอนเทนเนอร์ / หน้าจอ

```python
box = lv.obj(scr)
box.set_size(120, 80)
box.align(lv.ALIGN.CENTER, 0, 0)
box.set_style_bg_color(lv.color_hex(0x333333), 0)
box.set_style_radius(8, 0)
```

เมธอดหลัก: `set_pos, set_size, set_x/y, set_width/height, align, align_to,
center, add_flag, remove_flag, add_state, remove_state, add_style, set_style_*,
set_scrollbar_mode, get_child, get_parent, delete, move_foreground, move_background`

### 9.2 `lv.label` — ข้อความ

```python
lbl = lv.label(scr)
lbl.set_text('Line 1\nLine 2')
lbl.set_long_mode(lv.label.LONG_MODE.WRAP)
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.align(lv.ALIGN.TOP_LEFT, 8, 8)
```

เมธอด: `set_text, get_text, set_long_mode` (`lv.label.LONG_MODE.WRAP/DOTS/SCROLL/
SCROLL_CIRCULAR/CLIP`), `set_recolor`

### 9.3 `lv.button` — ปุ่มกด

```python
btn = lv.button(scr)
btn.set_size(160, 60)
btn.align(lv.ALIGN.CENTER, 0, -40)
lbl = lv.label(btn)
lbl.set_text('CLICK ME')
lbl.center()

def on_click(e):
    if e.get_code() == lv.EVENT.CLICKED:
        print('clicked')

btn.add_event_cb(on_click, lv.EVENT.ALL, None)
```

`lv.button` ไม่มีเมธอดเฉพาะ — ใช้อีเวนต์

### 9.4 `lv.slider` — แถบเลื่อนค่า

```python
slider = lv.slider(scr)
slider.set_range(0, 100)
slider.set_value(50, 0)          # (value, anim_en) — ใช้ 0 เพราะไม่มี ANIM_OFF
slider.set_size(220, 20)
slider.align(lv.ALIGN.CENTER, 0, 40)
print(slider.get_value())
```

เมธอด: `set_value(x, anim_en), get_value, set_range(min, max), set_min_value,
set_max_value, set_mode(lv.slider.MODE.NORMAL/SYMMETRICAL/RANGE),
set_orientation(lv.slider.ORIENTATION.HORIZONTAL/VERTICAL), is_dragged`

### 9.5 `lv.switch` — สวิตช์เปิด/ปิด

```python
sw = lv.switch(scr)
sw.align(lv.ALIGN.CENTER, 0, 0)

def on_sw(e):
    if e.get_code() == lv.EVENT.VALUE_CHANGED:
        on = sw.has_state(lv.STATE.CHECKED)
        print('switch is', 'ON' if on else 'OFF')

sw.add_event_cb(on_sw, lv.EVENT.ALL, None)
```

อ่านสถานะด้วย `sw.has_state(lv.STATE.CHECKED)`; ตั้งด้วย `sw.add_state` /
`sw.remove_state`

### 9.6 `lv.bar` — แถบความคืบหน้า

```python
bar = lv.bar(scr)
bar.set_range(0, 100)
bar.set_value(30, 0)
bar.set_size(200, 16)
bar.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.7 `lv.arc` — ส่วนโค้ง / ปุ่มหมุน

```python
arc = lv.arc(scr)
arc.set_size(140, 140)
arc.set_bg_angles(0, 360)
arc.set_rotation(270)
arc.set_value(30)
arc.align(lv.ALIGN.CENTER, 0, 0)
print(arc.get_value())
```

### 9.8 `lv.checkbox`

```python
cb = lv.checkbox(scr)
cb.set_text('Enable')
cb.align(lv.ALIGN.TOP_LEFT, 12, 12)
```

### 9.9 `lv.dropdown`

```python
dd = lv.dropdown(scr)
dd.set_options('Red\nGreen\nBlue')
dd.set_selected(0)               # (index)
dd.align(lv.ALIGN.TOP_LEFT, 12, 12)
print(dd.get_selected())         # 0
print(dd.get_text())
```

### 9.10 `lv.roller`

```python
roller = lv.roller(scr)
roller.set_options('1\n2\n3\n4\n5', lv.roller.MODE.NORMAL)
roller.set_visible_row_count(3)
roller.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.11 `lv.textarea` — ช่องกรอกข้อความ

```python
ta = lv.textarea(scr)
ta.set_one_line(True)
ta.set_placeholder_text('type here')
ta.set_max_length(32)
ta.set_size(200, 40)
ta.align(lv.ALIGN.CENTER, 0, 0)
# ta.get_text()
```

### 9.12 `lv.keyboard` — คีย์บอร์ดบนจอ

```python
kb = lv.keyboard(scr)
kb.set_textarea(ta)              # พิมพ์ลง textarea
kb.set_mode(lv.keyboard.MODE.TEXT_LOWER)
```

`lv.keyboard.MODE`: `TEXT_LOWER, TEXT_UPPER, SPECIAL, NUMBER`

### 9.13 `lv.table`

```python
tbl = lv.table(scr)
tbl.set_column_count(3)
tbl.set_row_count(3)
tbl.set_cell_value(0, 0, 'Name')
tbl.set_cell_value(0, 1, 'Value')
tbl.set_cell_value(1, 0, 'Temp')
tbl.set_cell_value(1, 1, '23')
tbl.set_size(280, 160)
tbl.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.14 `lv.tabview` — หน้าจอแบบแท็บ

```python
tv = lv.tabview(scr)
tab1 = tv.add_tab('Tab 1')
tab2 = tv.add_tab('Tab 2')
lv.label(tab1).set_text('page one')
lv.label(tab2).set_text('page two')
tv.set_active(0, 0)
```

### 9.15 `lv.chart` — กราฟ

```python
chart = lv.chart(scr)
chart.set_type(lv.chart.TYPE.LINE)
chart.set_point_count(20)
chart.set_axis_range(lv.chart.AXIS.PRIMARY_Y, 0, 100)
ser = chart.add_series(lv.palette_main(lv.PALETTE.BLUE), lv.chart.AXIS.PRIMARY_Y)
chart.set_next_value(ser, 42)     # เพิ่มค่าตัวอย่างใหม่
chart.set_size(280, 150)
chart.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.16 `lv.spinner` — ตัวบอกกิจกรรม

```python
sp = lv.spinner(scr)
sp.set_size(60, 60)
sp.set_anim_params(1000, 200)     # (time, delay)
sp.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.17 `lv.led`

```python
led = lv.led(scr)
led.set_color(lv.palette_main(lv.PALETTE.GREEN))
led.set_brightness(200)
led.on()
led.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.18 `lv.list` / `lv.list.add_button`

```python
lst = lv.list(scr)
lst.set_size(200, 160)
btn = lst.add_button(lv.SYMBOL.SETTINGS, 'Settings')
lst.add_text('About')
lst.align(lv.ALIGN.CENTER, 0, 0)
```

### 9.19 `lv.msgbox`

```python
mb = lv.msgbox(scr)
mb.add_title('Confirm')
mb.add_text('Save changes?')
ok = mb.add_footer_button('OK')
mb.add_footer_button('Cancel')

def on_ok(e):
    if e.get_code() == lv.EVENT.CLICKED:
        print('OK pressed')

ok.add_event_cb(on_ok, lv.EVENT.CLICKED, None)
```

### 9.20 `lv.image` / `lv.imagebutton` / `lv.animimg`

```python
img = lv.image(scr)          # ตั้งซอร์สภายหลัง: img.set_src(...)
ib  = lv.imagebutton(scr)    # ib.set_src(state, left, mid, right)
an  = lv.animimg(scr)        # an.set_src(dsc, count); an.start()
```

> ซอร์สของรูปใน binding นี้ต้องใช้ image descriptor ของ LVGL เป็นหัวข้อขั้นสูง
> เมธอดของวิดเจ็ต (`set_src`, `set_scale`, `set_rotation`, `set_offset_x/y`,
> `set_pivot`) มีให้ใช้

### 9.21 วิดเจ็ตอื่นที่มี

`lv.win`, `lv.menu` / `lv.menu_page`, `lv.line`, `lv.scale`, `lv.spinbox`,
`lv.spangroup`, `lv.tileview`, `lv.calendar`, `lv.buttonmatrix`, `lv.arclabel`
รายการทั้งหมดและทุกเมธอดอยู่ใน `lvgl.pyi` ในรีโปต้นทาง

---

## 10. อีเวนต์ (Events)

ผูก callback ด้วย `add_event_cb(callback, filter, user_data)`:

```python
def handler(e):
    code = e.get_code()
    if code == lv.EVENT.CLICKED:
        print('clicked, target:', e.get_target_obj())
        print('user data:', e.get_user_data())

obj.add_event_cb(handler, lv.EVENT.ALL, some_data)
```

- `filter` ปกติใช้ `lv.EVENT.ALL` หรือรหัสใดรหัสหนึ่ง
- `user_data` จะถูกคืนกลับทาง `e.get_user_data()`

### 10.1 รหัสอีเวนต์ที่พบบ่อย

| รหัส | เกิดเมื่อ |
| --- | --- |
| `lv.EVENT.PRESSED` | กดพอยน์เตอร์บนออบเจ็กต์ |
| `lv.EVENT.PRESSING` | กำลังกดค้าง/ลาก |
| `lv.EVENT.RELEASED` | ปล่อยพอยน์เตอร์ |
| `lv.EVENT.CLICKED` | คลิกเสร็จสมบูรณ์ |
| `lv.EVENT.LONG_PRESSED` | กดค้างนาน |
| `lv.EVENT.VALUE_CHANGED` | ค่าเปลี่ยน (slider, switch, arc, …) |
| `lv.EVENT.SCROLL_BEGIN` / `SCROLL_END` | การเลื่อน |
| `lv.EVENT.SCREEN_LOADED` / `SCREEN_UNLOADED` | สลับหน้าจอ |
| `lv.EVENT.DELETE` | ออบเจ็กต์กำลังถูกลบ |
| `lv.EVENT.ALL` | ตัวแทนทุกอีเวนต์ |

### 10.2 เมธอดของออบเจ็กต์อีเวนต์

| เมธอด | คืนค่า |
| --- | --- |
| `e.get_code()` | รหัสอีเวนต์ |
| `e.get_target_obj()` | ออบเจ็กต์ที่ทำให้เกิดอีเวนต์ (ใช้ตัวนี้) |
| `e.get_current_target_obj()` | ออบเจ็กต์ที่ผูก callback ไว้ |
| `e.get_user_data()` | `user_data` ที่ส่งให้ `add_event_cb` |
| `e.get_target()` | ค่าแบบ opaque — ควรใช้ `get_target_obj()` |

> ใน binding นี้ `e.get_target()` คืน blob แบบ opaque ที่ไม่มีเมธอดของวิดเจ็ต
> ให้ใช้ `e.get_target_obj()` หรืออ้างตัวแปรวิดเจ็ตที่ปิดไว้ (closure)

### 10.3 การอ่านจุดทัชใน callback

```python
def on_event(e):
    if e.get_code() == lv.EVENT.PRESSING:
        pt = lv.point_t()
        board.touch.get_point(pt)
        print(pt.x, pt.y)
```

---

## 11. สไตล์ (Styles)

มีสองวิธี: ตั้งพรอเพอร์ตีบนออบเจ็กต์ตรง ๆ หรือสร้าง `lv.style_t` ที่ใช้ซ้ำได้แล้ว
`add_style`

### 11.1 ตั้งตรง (พบบ่อยที่สุด)

```python
obj.set_style_bg_color(lv.color_hex(0x202020), 0)
obj.set_style_bg_opa(lv.OPA.COVER, 0)
obj.set_style_radius(8, 0)
obj.set_style_border_width(2, 0)
obj.set_style_border_color(lv.color_hex(0xFFFFFF), 0)
obj.set_style_pad_all(8, 0)
obj.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
obj.set_style_text_font(lv.font_montserrat_14, 0)
```

อาร์กิวเมนต์ที่สองคือ **selector** (`lv.PART.* | lv.STATE.*`) ค่า `0` หมายถึง
`PART.MAIN` ในสถานะเริ่มต้น ตัวอย่าง: `lv.PART.INDICATOR | lv.STATE.PRESSED`

### 11.2 สไตล์ที่ใช้ซ้ำได้

```python
style = lv.style_t()
style.init()
style.set_bg_color(lv.color_hex(0x004080))
style.set_bg_opa(lv.OPA.COVER)
style.set_radius(6)
style.set_pad_all(10)

btn.add_style(style, 0)
btn.remove_style(style, 0)
```

### 11.3 พรอเพอร์ตี `set_style_*` ที่พบบ่อยบนออบเจ็กต์

พื้นหลัง: `bg_color, bg_opa, bg_grad_color, bg_grad_dir`
ขอบ: `border_color, border_width, border_opa, border_side`
เส้นรอบนอก: `outline_color, outline_width, outline_pad`
เงา: `shadow_color, shadow_width, shadow_offset_x/y, shadow_spread`
ข้อความ: `text_color, text_font, text_letter_space, text_line_space, text_align`
ขนาด/ระยะ: `width, height, min_width, max_width, radius, pad_all, pad_hor,
pad_ver, pad_left/right/top/bottom, margin_all, x, y`
อื่น ๆ: `opa, clip_corner, transform_scale, transform_rotation, blend_mode,
recolor, recolor_opa`

`lv.RADIUS_CIRCLE` (= 32767) ทำให้ออบเจ็กต์กลมเต็มวง (ไม่ใช่ `lv.RADIUS.CIRCLE`)

---

## 12. โมดูลระบบ

### 12.1 `machine` — พิน, บัส, ตัวจับเวลา

```python
import machine
p = machine.Pin(21, machine.Pin.OUT)
p.value(1)
pwm = machine.PWM(p, freq=38000)
pwm.duty_u16(32768)

spi = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
tim = machine.Timer(0)
```

### 12.2 `network` — Wi-Fi

```python
import network

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect('SSID', 'password')          # เชื่อมต่อแบบ STA
# sta.ifconfig()                         # (ip, netmask, gateway, dns)
# sta.isconnected()

ap = network.WLAN(network.AP_IF)         # ทำเป็นจุดกระจายสัญญาณ
ap.active(True)
ap.config(essid='CYD', password='12345678')
```

ตัวอย่างสแกน (ดู [§13.6](#136-สแกน-wi-fi)):

```python
for ssid, bssid, ch, rssi, sec, hidden in sta.scan():
    print(ssid, rssi, ch)
```

### 12.3 `time`, `machine.Timer`, `gc`

```python
import time, gc
time.sleep(1); time.sleep_ms(10); time.sleep_us(100)
time.ticks_ms(); time.ticks_diff(t2, t1)
gc.collect(); gc.mem_free()
```

### 12.4 `esp32`

```python
import esp32
esp32.raw_temperature()      # อุณหภูมิภายใน (ฟาเรนไฮต์)
esp32.wake_on_touch(True)
```

---

## 13. โปรแกรมตัวอย่างแบบเต็ม

บันทึกแล้วรันด้วย `mpremote run <ไฟล์>` หรือใช้ `tests/run.sh`

### 13.1 Hello, CYD

```python
import lvgl as lv, lcd_bus, time
import display                       # เริ่มต้นบอร์ด

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x001030), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

lbl = lv.label(scr)
lbl.set_text('Hello, CYD!')
lbl.set_style_text_font(lv.font_montserrat_16, 0)
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.center()
scr.invalidate()

while True:
    lcd_bus._pump_main_thread()
    time.sleep_ms(10)
```

### 13.2 ปุ่มนับครั้ง

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x101018), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

count = 0
cl = lv.label(scr); cl.set_text('taps: 0'); cl.align(lv.ALIGN.TOP_MID, 0, 10)

def on_btn(e):
    global count
    if e.get_code() == lv.EVENT.CLICKED:
        count += 1
        cl.set_text('taps: %d' % count)

btn = lv.button(scr); btn.set_size(160, 60); btn.align(lv.ALIGN.CENTER, 0, 0)
lv.label(btn).set_text('TAP ME')
btn.add_event_cb(on_btn, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.3 สไลเดอร์ขับแถบ bar

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

bar = lv.bar(scr); bar.set_range(0, 100); bar.set_value(0, 0)
bar.set_size(240, 20); bar.align(lv.ALIGN.CENTER, 0, -40)

slider = lv.slider(scr); slider.set_range(0, 100); slider.set_value(0, 0)
slider.set_size(240, 20); slider.align(lv.ALIGN.CENTER, 0, 20)

def on_slider(e):
    if e.get_code() == lv.EVENT.VALUE_CHANGED:
        bar.set_value(slider.get_value(), 0)

slider.add_event_cb(on_slider, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.4 สวิตช์เปลี่ยนสีกล่อง

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

box = lv.obj(scr); box.set_size(100, 100); box.align(lv.ALIGN.CENTER, 0, -40)
box.set_style_bg_opa(lv.OPA.COVER, 0); box.set_style_radius(8, 0)
box.set_style_bg_color(lv.color_hex(0x444444), 0)

sw = lv.switch(scr); sw.align(lv.ALIGN.CENTER, 0, 50)

def on_sw(e):
    if e.get_code() == lv.EVENT.VALUE_CHANGED:
        if sw.has_state(lv.STATE.CHECKED):
            box.set_style_bg_color(lv.color_hex(0x00C000), 0)
        else:
            box.set_style_bg_color(lv.color_hex(0x444444), 0)
        box.invalidate()

sw.add_event_cb(on_sw, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.5 วาดจุดตามนิ้ว

```python
import lvgl as lv, lcd_bus, time
import board

board.calibrate_touch()
W, H = board.size()
scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

dot = lv.obj(scr); dot.set_size(28, 28)
dot.set_style_bg_color(lv.color_hex(0x00FF00), 0)
dot.set_style_bg_opa(lv.OPA.COVER, 0)
dot.set_style_radius(lv.RADIUS_CIRCLE, 0)
dot.set_style_border_width(0, 0)
dot.add_flag(lv.obj.FLAG.HIDDEN)

def on_event(e):
    code = e.get_code()
    if code == lv.EVENT.PRESSING:
        pt = lv.point_t()
        board.touch.get_point(pt)
        dot.set_pos(pt.x - 14, pt.y - 14)
        dot.remove_flag(lv.obj.FLAG.HIDDEN)
    elif code == lv.EVENT.RELEASED:
        dot.add_flag(lv.obj.FLAG.HIDDEN)

area = lv.obj(scr); area.set_size(W, H); area.set_pos(0, 0)
area.set_style_bg_opa(lv.OPA.TRANSP, 0)
area.set_style_border_width(0, 0)
area.add_flag(lv.obj.FLAG.CLICKABLE)
area.add_event_cb(on_event, lv.EVENT.ALL, None)
scr.invalidate()

while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

### 13.6 สแกน Wi-Fi

```python
import network

sta = network.WLAN(network.STA_IF)
sta.active(True)
print('scanning...')
for ssid, bssid, ch, rssi, sec, hidden in sorted(sta.scan(), key=lambda n: n[3], reverse=True):
    print('%-24s %4d dBm  ch %d' % (
        ssid.decode() if isinstance(ssid, bytes) else ssid, rssi, ch))
```

### 13.7 แท็บที่มีสไลเดอร์และปุ่ม

```python
import lvgl as lv, lcd_bus, time
import display

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)
scr.set_style_bg_opa(lv.OPA.COVER, 0)

tv = lv.tabview(scr)
p1 = tv.add_tab('Slider')
p2 = tv.add_tab('Button')

s = lv.slider(p1); s.set_range(0, 100); s.set_value(10, 0)
s.set_width(200); s.center()

b = lv.button(p2); b.set_size(140, 50); b.center()
lv.label(b).set_text('PRESS')

def on_b(e):
    if e.get_code() == lv.EVENT.CLICKED:
        print('pressed on tab 2')
b.add_event_cb(on_b, lv.EVENT.ALL, None)

scr.invalidate()
while True:
    lcd_bus._pump_main_thread(); time.sleep_ms(10)
```

---

## 14. จุดสังเกต/ข้อควรระวังของ binding

| หัวข้อ | ใช้แบบนี้ | อย่าใช้ |
| --- | --- | --- |
| แฟล็กออบเจ็กต์ | `lv.obj.FLAG.HIDDEN`, `add_flag` / `remove_flag` | `lv.OBJ_FLAG.*`, `clear_flag` |
| รัศมีกลม | `lv.RADIUS_CIRCLE` | `lv.RADIUS.CIRCLE` |
| ค่าสไลเดอร์ | `slider.set_value(v, 0)` | `lv.ANIM_OFF` (ไม่มี) |
| เรียกในอีเวนต์ cb | `board.touch.get_point(pt)` | `lv.indev_active()` (อาจเป็น `None`) |
| เป้าหมายอีเวนต์ | `e.get_target_obj()` | `e.get_target()` (opaque) |
| ตัวอย่างเก่า | `lv.img`, `lv.imgbtn` | ใช้ `lv.image`, `lv.imagebutton` (ชื่อ LVGL 9) |
| มิเตอร์ | — | `lv.meter` ไม่มี (LVGL 9 ใช้ `lv.scale`) |
| สร้าง indev | `import display` (ครั้งเดียวต่อรอบไฟ) | `import display` ซ้ำหลัง soft reset |

- อาร์กิวเมนต์ของคอนสตรัคเตอร์เป็น **positional-only** *ชื่อ* พารามิเตอร์ในสตับถูก
  สร้างอัตโนมัติและบางครั้งไม่มีความหมาย ให้เรียกแบบตำแหน่ง
- LVGL 9 เปลี่ยนชื่อหลายอย่างเทียบบทเรียนเก่า: `lv.image` (เดิม `lv.img`),
  `lv.imagebutton` (เดิม `lv.imgbtn`), `lv.spangroup` (เดิม `lv.span`)
- มีฟอนต์ในตัวเฉพาะ Montserrat 12/14/16

---

## 15. การแก้ปัญหา

| อาการ | สาเหตุ / วิธีแก้ |
| --- | --- |
| `TypeError: can't convert str to int` ใน `display.py` | `import display` ซ้ำในรอบไฟเดียวกัน — ให้ hard reset ก่อน |
| จอดำ | แบ็คไลต์เป็น 0 — เรียก `board.backlight(100)`; ตรวจว่าแฟลชสำเร็จ |
| สีผิด (แดงกลายเป็นน้ำเงิน) | อิมเมจถูก build โดยไม่มี BGR — ใช้ `firmware/*.bin` ที่ให้มา |
| ภาพเบี้ยว / แถบดำ / กลับด้าน | `_ORIENTATION_TABLE` / `display_width` ผิด — ใช้เฟิร์มแวร์ที่ให้มา |
| ทัชเพี้ยนไป ~80 px | คาลิเบรต fit ไปที่พิกัดจอ แทนพิกัดก่อนการหมุน — ใช้ `board.calibrate_touch()` |
| ทัชไม่ตอบสนอง | ยังไม่คาลิเบรต (`board.touch.is_calibrated`) หรือลืม `touch.enable(True)` |
| UI ค้างทันทีหลังสคริปต์จบ | `mpremote run` คืนค่าแล้ว — เติมลูป `while True: lcd_bus._pump_main_thread()` |
| `MemoryError` | พาร์ทิชันแอปเต็ม — ลดวิดเจ็ต/ฟีเจอร์ แล้ว build ใหม่ |
| `AttributeError` ที่เมธอดวิดเจ็ต | ชื่อต่างใน binding นี้ — ตรวจ `lvgl.pyi` |

---

## 16. ชุดทดสอบ

`tests/` มีสคริปต์แบบสแตนด์อโลน (ไม่ได้ build เข้าเฟิร์มแวร์) ให้ใช้ตัวห่อ ซึ่งจะ
hard reset บอร์ดก่อน (จำเป็น ดู [§4](#4-โมดูล-display-ที่-freeze-ไว้)):

```bash
cd tests
./run.sh boot_check.py       # ทดสอบเบื้องต้น
./run.sh test_pattern.py     # ความครอบคลุม / การวางแนว / สี
./run.sh test_display.py
./run.sh test_backlight.py
./run.sh test_touch.py       # ต้องแตะ
./run.sh test_lvgl.py        # ต้องแตะ
./run.sh test_wifi.py
```

ตั้งพอร์ตถ้าจำเป็น:

```bash
CYD_PORT=/dev/cu.usbserial-0001 ./run.sh test_display.py
```

การทดสอบแบบโต้ตอบ (`test_touch.py`, `test_lvgl.py`) จบท้ายด้วยลูป polling เพื่อให้
LVGL ทำงานต่อ หยุดด้วย `Ctrl-C`

---

## 17. การ build เฟิร์มแวร์ใหม่

ดูคู่มือ build ในรีโปต้นทาง:

- `lvgl_micropython/AGENTS.md` — รายละเอียดการ build/TOML/การแฟลชทั้งหมด
- `AGENTS.md` (รากรีโป) — ภาพรวมโปรเจกต์และจุดสำคัญ

คำสั่ง build (ครั้งแรกใช้เวลา ~15–30 นาที):

```bash
python3 make.py esp32 --toml display_configs/CYD-2432S028R.toml --ccache --no-scrub
```

ผลลัพธ์: `build/lvgl_micropy_ESP32_GENERIC-4.bin` (แฟลชที่ `0x0`)

---

*MicroPython 1.27.0 · LVGL 9.4.0 · ESP-IDF 5.5.1 · บอร์ด ESP32-2432S028R*
