#!/usr/bin/env bash
#
# run.sh - hard-reset the CYD and run one MicroPython test script.
#
# Why a hard reset: mpremote soft-resets the board on every connect, but an
# ESP32 SPI host created by `import display` is *not* released by a soft
# reset. Re-running a test in the same power cycle therefore fails when
# display.py re-creates the SPI bus. A real (DTR/RTS) reset clears it.
#
# Usage:
#   ./run.sh <script.py>            e.g. ./run.sh test_display.py
#
# Environment:
#   CYD_PORT  serial port   (default /dev/cu.wchusbserial2110)
#   MPY_PY    python w/ pyserial + mpremote (default python3)
#
set -euo pipefail

PORT="${CYD_PORT:-/dev/cu.wchusbserial2110}"
PY="${MPY_PY:-python3}"
SCRIPT="${1:?usage: run.sh <script.py>}"

# Scripts live next to this file.
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/${SCRIPT#./}"

"$PY" - "$PORT" <<'PYEOF'
import sys
import time
import serial

p = serial.Serial(sys.argv[1], 115200)
try:
    p.write(b'\x03')                  # cancel anything that is running
    p.setDTR(False)
    p.setRTS(True)                    # assert reset
    time.sleep(0.15)
    p.setRTS(False)                   # release -> board boots
finally:
    p.close()
time.sleep(2.0)
PYEOF

# Make sure board.py / any helper modules / font are on the device.
"$PY" -m mpremote connect "$PORT" cp "$(dirname "$SCRIPT_PATH")/board.py" :board.py >/dev/null
for _m in thai.py fonts/Sarabun-Regular.ttf; do
    _p="$(dirname "$SCRIPT_PATH")/$_m"
    [ -f "$_p" ] && "$PY" -m mpremote connect "$PORT" cp "$_p" ":$(basename "$_m")" >/dev/null
done

exec "$PY" -m mpremote connect "$PORT" run "$SCRIPT_PATH"
