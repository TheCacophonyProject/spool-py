# Program 5: LED indicator test — no spool triggering.
# led1 (PIR trigger): lights for HOLD_MS on either PIR rising edge.
# led2 (thermal trigger): lights for HOLD_MS when MLX90640 detects motion.

import math
import time
import array
from machine import I2C, Pin
from mlx90640 import MLX90640
from util import PIRs
from config import *

i2c  = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=1_000_000)
led1 = Pin(PIN_LED_1, Pin.OUT, value=0)
led2 = Pin(PIN_LED_2, Pin.OUT, value=0)
pirs = PIRs(i2c)    ## This will set the sensitivity of the PIRs

HOLD_MS = 500

# ------------------------------------------------------------ LED hold timers --

_led1_t = [0]
_led2_t = [0]

def _update_leds():
    now = time.ticks_ms()
    if led1.value() and time.ticks_diff(_led1_t[0], now) <= 0:
        led1.off()
    if led2.value() and time.ticks_diff(_led2_t[0], now) <= 0:
        led2.off()

# ----------------------------------------------------------------------- PIR --

def _pir_irq(pin):
    _led1_t[0] = time.ticks_add(time.ticks_ms(), HOLD_MS)
    led1.on()
    print("PIR triggered")

Pin(PIN_PIR_1, Pin.IN, Pin.PULL_DOWN).irq(trigger=Pin.IRQ_RISING, handler=_pir_irq)
Pin(PIN_PIR_2, Pin.IN, Pin.PULL_DOWN).irq(trigger=Pin.IRQ_RISING, handler=_pir_irq)

# ------------------------------------------------------------------- Thermal --

sensor = MLX90640(i2c)
sensor.set_chess_mode()
sensor.set_refresh_rate(MLX_REFRESH_HZ)
print("Loading MLX90640 calibration...")
sensor.load_calibration()
print("Ready. threshold={:.1f}, border={}".format(MLX_THRESHOLD, MLX_BORDER))

prev = [None, None]

def _check_thermal():
    fd, sp = sensor.get_frame_data()
    curr = sensor.calculate_raw(fd, sp, border=MLX_BORDER)
    if prev[sp] is None:
        prev[sp] = array.array('f', curr)
        return
    total    = 0.0
    total_sq = 0.0
    mx       = -1e9
    n        = 0
    for row in range(MLX_BORDER, 24 - MLX_BORDER):
        row_base = row << 5
        il_pat = row & 1
        for col in range(MLX_BORDER, 32 - MLX_BORDER):
            if (il_pat ^ (col & 1)) != sp:
                continue
            c = curr[row_base | col]
            if c == 0.0:
                continue
            d = c - prev[sp][row_base | col]
            if d < 0: d = -d
            total    += d
            total_sq += d * d
            if d > mx: mx = d
            n += 1
    prev[sp][:] = curr
    if n == 0:
        return
    mean   = total / n
    stddev = math.sqrt(total_sq / n - mean * mean)
    print("max={:.2f}  mean={:.2f}  stddev={:.2f}{}".format(
        mx, mean, stddev, "  TRIGGER" if mean > MLX_THRESHOLD else ""))
    if mean > MLX_THRESHOLD or mx > 30 or stddev > 6:
        _led2_t[0] = time.ticks_add(time.ticks_ms(), HOLD_MS)
        led2.on()

# ----------------------------------------------------------------- main loop --

while True:
    _update_leds()
    _check_thermal()
