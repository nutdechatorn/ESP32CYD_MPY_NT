#!/usr/bin/env bash
#
# build.sh - build a CYD firmware variant from display_configs/CYD-2432S028R.toml.
#
#   ./build.sh en    English / ASCII only  (TinyTTF disabled, smallest image)
#   ./build.sh th    English + Thai        (TinyTTF enabled, ~65 KB larger)
#
# The only difference is the MICROPY_TINY_TTF define, which lv_conf.h maps to
# LV_USE_TINY_TTF. It must be passed via LV_CFLAGS (not by editing lv_conf.h) so
# that both the C compile *and* the LVGL MicroPython binding generator see it.
#
# Output is copied to build/lvgl_micropy_CYD-<variant>.bin
#
set -euo pipefail
cd "$(dirname "$0")"

variant="${1:-en}"
case "$variant" in
    en)      extra=() ;;
    th|thai) extra=('LV_CFLAGS=-DMICROPY_TINY_TTF=1') ;;
    *) echo "usage: $0 {en|th}" >&2; exit 2 ;;
esac

python3 make.py esp32 ${extra[@]+"${extra[@]}"} \
    --toml display_configs/CYD-2432S028R.toml --ccache --no-scrub

out="build/lvgl_micropy_CYD-${variant}.bin"
cp build/lvgl_micropy_ESP32_GENERIC-4.bin "$out"
echo "==> $out"
