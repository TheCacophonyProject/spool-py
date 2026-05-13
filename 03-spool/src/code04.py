# Program 4: trap triggering with time-based active window.
# Set TRIGGER_SOURCE in config.py to "thermal" (MLX90640) or "pir" (PIR interrupts).
# PIR LED (led1) is always active regardless of TRIGGER_SOURCE.

import time
import array
from machine import I2C, Pin
from util import Spool, Clock, PIRs
from config import *

i2c   = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=400_000)
spool = Spool(i2c)
clock = Clock(i2c)
led1  = Pin(PIN_LED_1, Pin.OUT, value=0)   # PIR
led2  = Pin(PIN_LED_2, Pin.OUT, value=0)   # thermal
pirs = PIRs(i2c)

HOLD_MS = 500

# ------------------------------------------------------------ LED hold timers --

_led1_t = [0]   # ticks_ms deadline for led1
_led2_t = [0]   # ticks_ms deadline for led2

def _update_leds():
    now = time.ticks_ms()
    if led1.value() and time.ticks_diff(_led1_t[0], now) <= 0:
        led1.off()
    if led2.value() and time.ticks_diff(_led2_t[0], now) <= 0:
        led2.off()

# ----------------------------------------------------------------- PIR mode --

_pir_triggered = [False]

def _pir_irq(pin):
    _led1_t[0] = time.ticks_add(time.ticks_ms(), HOLD_MS)
    print("PIR triggered")
    led1.on()
    if TRIGGER_SOURCE == "pir":
        _pir_triggered[0] = True

# Always install PIR interrupt so led1 lights up in any mode.
Pin(PIN_PIR_1, Pin.IN, Pin.PULL_DOWN).irq(trigger=Pin.IRQ_RISING, handler=_pir_irq)
Pin(PIN_PIR_2, Pin.IN, Pin.PULL_DOWN).irq(trigger=Pin.IRQ_RISING, handler=_pir_irq)

def _pir_motion_detected(prev):
    if _pir_triggered[0]:
        _pir_triggered[0] = False
        return True
    return False

# ------------------------------------------------------------ Thermal mode --

def _setup_thermal():
    from mlx90640 import MLX90640
    global _sensor
    _sensor = MLX90640(i2c)
    _sensor.set_chess_mode()
    _sensor.set_refresh_rate(MLX_REFRESH_HZ)
    print("Loading MLX90640 calibration...")
    _sensor.load_calibration()
    print("MLX90640 ready. threshold={:.1f}, border={}".format(MLX_THRESHOLD, MLX_BORDER))

def _thermal_motion_detected(prev):
    fd, sp = _sensor.get_frame_data()
    curr = _sensor.calculate_raw(fd, sp, border=MLX_BORDER)
    if prev[sp] is None:
        prev[sp] = array.array('f', curr)
        return False
    total = 0.0
    n = 0
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
            total += d
            n += 1
    prev[sp][:] = curr
    if n > 0 and (total / n) > MLX_THRESHOLD:
        _led2_t[0] = time.ticks_add(time.ticks_ms(), HOLD_MS)
        led2.on()
        return True
    return False

# ------------------------------------------------------------------- setup --

if TRIGGER_SOURCE == "pir":
    print("PIR trigger ready.")
    def motion_detected(prev):
        return _pir_motion_detected(prev)
elif TRIGGER_SOURCE == "thermal":
    _setup_thermal()
    def motion_detected(prev):
        return _thermal_motion_detected(prev)
else:
    raise ValueError("TRIGGER_SOURCE must be 'pir' or 'thermal'")

# ---------------------------------------------------------------- main loop --

while True:
    led1.off()
    led2.off()
    print("Resetting")
    spool.reset_sequence()
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)

    print("Waiting for {} to detect motion during the active window.".format(TRIGGER_SOURCE))
    prev = [None, None]
    old_state = ""
    while True:
        _update_leds()
        if clock.in_active_window():
            if motion_detected(prev):
                print("active and motion detected")
                break
            state = "active, no motion"
        else:
            if motion_detected(prev):
                state = "inactive, motion"
            else:
                state = "inactive, no motion"

        if state != old_state:
            print(state)
            old_state = state

    print("Motion detected, releasing spool.")
    spool.release()
    time.sleep(2)

    print("Waiting 10 minutes until resetting")
    time.sleep(10 * 60)
