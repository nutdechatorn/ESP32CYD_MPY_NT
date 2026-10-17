"""
board.py - shared helper for the CYD test scripts.

Importing this module brings the hardware up, because it does `import display`.

The frozen `display` module was generated from
`lvgl_micropython/display_configs/CYD-2432S028R.toml` and wires up:

    display.display -> ILI9341 320x240   (SPI host1, DC=2, CS=15, BL=21)
    display.indev   -> XPT2046 touch     (SPI host2, CS=33, IRQ=36)
    task_handler.TaskHandler() -> pumps LVGL timers/flush

So `import display` is all it takes to initialise the panel + touch.
"""

import display
import lvgl as lv

# The ILI9341 driver instance (also the LVGL display driver).
lcd = display.display

# The XPT2046 pointer driver instance.
touch = display.indev


def width():
    return lcd.get_horizontal_resolution()


def height():
    return lcd.get_vertical_resolution()


def size():
    return width(), height()


def backlight(level=100):
    """Set backlight brightness 0-100 (%)."""
    lcd.set_backlight(level)


def _solve3(m, r):
    """Solve a 3x3 linear system by Cramer's rule. m is 3x3, r length 3."""

    def det3(a):
        return (
            a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) -
            a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0]) +
            a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
        )

    d = det3(m)
    if d == 0:
        return None

    out = []
    for col in range(3):
        mm = [row[:] for row in m]
        for row in range(3):
            mm[row][col] = r[row]
        out.append(det3(mm) / d)
    return out


def _lvgl_rotation_inverse(tx, ty, rotation, w, h):
    """
    Invert the pointer transform LVGL applies in `indev_pointer_proc`
    (lib/lvgl/src/indev/lv_indev.c). Given a desired on-screen coordinate
    (in the *current* rotation), return the coordinate the indev driver must
    supply *before* LVGL rotates it, i.e. the value `_calc_coords` should
    produce.

    `w, h` are the current (rotated) display dims as reported by the public
    API. LVGL's transform uses the internal `disp->hor_res/ver_res`, which are
    the *unrotated* (native) dims, so for rotations 90/270 the base dims are
    swapped relative to `w, h`.
    """
    if rotation == lv.DISPLAY_ROTATION._90 or rotation == lv.DISPLAY_ROTATION._270:
        bw, bh = h, w
    else:
        bw, bh = w, h

    if rotation == lv.DISPLAY_ROTATION._90:
        return ty, bh - 1 - tx
    if rotation == lv.DISPLAY_ROTATION._180:
        return bw - 1 - tx, bh - 1 - ty
    if rotation == lv.DISPLAY_ROTATION._270:
        return bw - 1 - ty, tx
    return tx, ty


def _fit_plane(samples):
    """Least-squares fit w ~= a*u + b*v + c. samples is a list of (u, v, w)."""
    n = len(samples)
    suu = suv = svv = su = sv = sw = swu = swv = 0.0
    for u, v, w in samples:
        suu += u * u
        suv += u * v
        svv += v * v
        su += u
        sv += v
        sw += w
        swu += w * u
        swv += w * v

    m = [[suu, suv, su], [suv, svv, sv], [su, sv, float(n)]]
    return _solve3(m, [swu, swv, sw])


def calibrate_touch(force=False):
    """
    Interactive 5-point touch calibration, run in the *current* display
    rotation (landscape 320x240).

    The frozen `indev.calibrate()` cannot be used here: it forces the display
    to rotation _0 while computing its target points from
    `indev._orig_width/_orig_height`, which are the landscape dims (320x240)
    because the indev is created after `set_rotation._90`. The targets then
    land off the portrait screen and the resulting affine is wrong.

    Here we keep the display as-is, tap a red square at four corners and the
    centre, then least-squares fit an affine raw->screen transform and save it
    to NVS.

    Note: LVGL applies the display rotation to pointer coordinates itself
    (`indev_pointer_proc` in lib/lvgl/src/indev/lv_indev.c), so the affine is
    fitted against the *pre-rotation* coordinates (see `_lvgl_rotation_inverse`)
    - otherwise every point is rotated a second time and lands wrong.
    """
    if touch.is_calibrated and not force:
        return True

    import time
    import lcd_bus

    def pump(ms):
        end = time.ticks_add(time.ticks_ms(), ms)
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            lcd_bus._pump_main_thread()
            time.sleep_ms(5)

    W, H = size()
    size_px = 30
    targets = [
        (40, 40), (W - 40, 40),
        (40, H - 40), (W - 40, H - 40),
        (W // 2, H // 2),
    ]

    scr = lv.obj()
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    for flag in (lv.obj.FLAG.CLICKABLE, lv.obj.FLAG.SCROLLABLE):
        scr.remove_flag(flag)

    target = lv.obj(scr)
    target.set_size(size_px, size_px)
    target.set_style_bg_color(lv.color_hex(0xFF0000), 0)
    target.set_style_bg_opa(lv.OPA.COVER, 0)
    target.set_style_radius(0, 0)
    target.set_style_border_width(0, 0)
    for flag in (lv.obj.FLAG.CLICKABLE, lv.obj.FLAG.SCROLLABLE):
        target.remove_flag(flag)

    label = lv.label(scr)
    label.align(lv.ALIGN.TOP_MID, 0, 4)

    old = lv.screen_active()
    lv.screen_load(scr)
    touch.enable(True)

    samples = []
    total = len(targets)
    for i, (tx, ty) in enumerate(targets):
        target.set_pos(tx - size_px // 2, ty - size_px // 2)
        label.set_text('Tap the RED square  (%d/%d)' % (i + 1, total))
        pump(300)

        while True:
            t = touch._get_coords()
            if t is not None and t[0]:
                samples.append((t[1], t[2]))
                break
            pump(30)

        label.set_text('OK  (%d/%d)' % (i + 1, total))
        while True:
            t = touch._get_coords()
            if t is None or not t[0]:
                break
            pump(30)
        pump(200)

    lv.screen_load(old)
    scr.delete()
    pump(100)

    # LVGL applies the display rotation to pointer coordinates a *second* time
    # in lib/lvgl/src/indev/lv_indev.c, so the affine must map raw -> the
    # pre-rotation coordinate that LVGL rotates to the screen position we asked
    # the user to tap.
    rotation = lcd.get_rotation()
    fit = [_lvgl_rotation_inverse(tx, ty, rotation, W, H) for tx, ty in targets]

    xs = _fit_plane([(samples[i][0], samples[i][1], fit[i][0]) for i in range(total)])
    ys = _fit_plane([(samples[i][0], samples[i][1], fit[i][1]) for i in range(total)])
    if xs is None or ys is None:
        print('calibration failed: singular fit')
        return False

    alphaX, betaX, deltaX = xs
    alphaY, betaY, deltaY = ys

    cal = touch._cal
    cal.alphaX = alphaX
    cal.betaX = betaX
    cal.deltaX = deltaX
    cal.alphaY = alphaY
    cal.betaY = betaY
    cal.deltaY = deltaY
    cal.mirrorX = False
    cal.mirrorY = False
    cal.save()

    print('rotation      :', rotation)
    print('targets screen:', targets)
    print('targets indev :', fit)
    print('raw samples   :', samples)
    print('coefficients  : aX=%.6f bX=%.6f dX=%.3f' % (alphaX, betaX, deltaX))
    print('                aY=%.6f bY=%.6f dY=%.3f' % (alphaY, betaY, deltaY))
    for i, (rx, ry) in enumerate(samples):
        ix = alphaX * rx + betaX * ry + deltaX
        iy = alphaY * rx + betaY * ry + deltaY
        print('  raw(%d,%d) -> indev(%.1f,%.1f) want(%d,%d) err %+.1f,%+.1f' % (
            rx, ry, ix, iy, fit[i][0], fit[i][1], ix - fit[i][0], iy - fit[i][1]))
    print('calibration saved:', touch.is_calibrated)
    return touch.is_calibrated


def reset_touch_cal():
    """Erase any saved touch calibration."""
    touch._cal.reset()


def dump_info():
    """Print a short hardware/firmware report to the serial console."""
    import sys
    import gc

    print('---- CYD board info ----')
    print('firmware  :', sys.version)
    print('display   :', width(), 'x', height())
    print('backlight :', lcd.get_backlight())
    print('touch cal :', touch.is_calibrated)
    gc.collect()
    print('free RAM  :', gc.mem_free(), 'bytes')
    print('------------------------')
