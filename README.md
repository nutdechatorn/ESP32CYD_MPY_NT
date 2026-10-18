# ESP32 Cheap Yellow Display (CYD) — MicroPython + LVGL

MicroPython **1.27.0** + **LVGL 9.4.0** firmware for the classic
**ESP32-2432S028R** Cheap Yellow Display (ESP32-WROOM-32, 4 MB flash, no PSRAM;
ILI9341 240×320 panel driven as 320×240 landscape, XPT2046 touch).

Two language variants are provided:

| Variant | Thai text | Merged image (esptool @ `0x0`) | Thonny image (@ `0x1000`) |
|---|---|---|---|
| English only | – | `firmware/en/esptool-0x0/...-en.bin` | `firmware/en/thonny-0x1000/...-en-thonny.bin` |
| English + Thai | ✅ TinyTTF + shaper | `firmware/th/esptool-0x0/...-th.bin` | `firmware/th/thonny-0x1000/...-th-thonny.bin` |

See [`firmware/README.md`](firmware/README.md) for download details, flashing
offsets and SHA256 checksums.

## Documentation

Full API reference with runnable examples:

- English — [`docs/manual.en.md`](docs/manual.en.md)
- ภาษาไทย — [`docs/manual.th.md`](docs/manual.th.md)

## Thai text

LVGL has no OpenType shaping, so Thai tone marks stacked over an upper vowel
collide. The English + Thai firmware enables TinyTTF, and
[`tests/thai.py`](tests/thai.py) is a small shaper that re-stacks the marks
using real glyph metrics. The font (`tests/fonts/Sarabun-Regular.ttf`) and
`thai.py` are copied to the board filesystem (the app partition is full):

```bash
mpremote connect PORT fs cp tests/thai.py :thai.py
mpremote connect PORT fs cp tests/fonts/Sarabun-Regular.ttf :Sarabun-Regular.ttf
```

Details: [`docs/manual.en.md` §8.6.1](docs/manual.en.md) and
[`tests/README.md`](tests/README.md).

## Rebuilding from source

```bash
cd lvgl_micropython
./build.sh en     # English only
./build.sh th     # English + Thai  (adds -DMICROPY_TINY_TTF=1)
```

Requires Python 3, `cmake`, `ninja`; ESP-IDF v5.5.1 is installed automatically
on first build. See [`lvgl_micropython/AGENTS.md`](lvgl_micropython/AGENTS.md)
for the full, verified build guide.

## Board tests

`tests/` holds standalone MicroPython scripts run over serial:

```bash
cd tests
./run.sh boot_check.py       # smoke test
./run.sh test_pattern.py     # coverage / orientation / colours
./run.sh test_thai.py        # Thai shaping (English + Thai firmware)
```

See [`tests/README.md`](tests/README.md).

## Repository layout

- `firmware/` — prebuilt images (English only, English + Thai)
- `docs/` — user manual (English / Thai)
- `lvgl_micropython/` — the build system and target config
- `tests/` — board test scripts and the Thai shaper
- `ESP32-Cheap-Yellow-Display/` — CYD hardware docs / pinout reference
