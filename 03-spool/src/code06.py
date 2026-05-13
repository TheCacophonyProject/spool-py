# Program 6: SNR measurement tool.
#
# Phase 1 - Baseline: collect BASELINE_SECS seconds of readings with nothing
#   moving. Computes noise floor mean (u) and stddev (s) from the per-frame
#   mean-abs-diff values.
#
# Phase 2 - Monitor: prints per-frame stats plus:
#   SNR    = current_mean / noise_mean   (how many times above noise floor)
#   z      = (current_mean - noise_mean) / noise_stddev  (sigma above noise)
#   A suggested threshold is printed after calibration: noise_mean + 3*noise_s
#
# Use this to find a good MLX_THRESHOLD value for code04/code05.

import math
import time
import array
from machine import I2C, Pin
from mlx90640 import MLX90640
from config import *

BASELINE_SECS = 10   # seconds of quiet baseline to collect

i2c    = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=1_000_000)
sensor = MLX90640(i2c)
sensor.set_chess_mode()
sensor.set_refresh_rate(MLX_REFRESH_HZ)
print("Loading MLX90640 calibration...")
sensor.load_calibration()
print("Ready. border={}".format(MLX_BORDER))

prev = [None, None]

def _frame_mean_diff():
    """Return mean abs-diff for the current frame, or None on first subpage."""
    fd, sp = sensor.get_frame_data()
    curr = sensor.calculate_raw(fd, sp, border=MLX_BORDER)
    if prev[sp] is None:
        prev[sp] = array.array('f', curr)
        return None, None, None
    total    = 0.0
    total_sq = 0.0
    mx       = 0.0
    n        = 0
    for row in range(MLX_BORDER, 24 - MLX_BORDER):
        row_base = row << 5
        il_pat   = row & 1
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
        return None, None, None
    mean   = total / n
    stddev = math.sqrt(max(0.0, total_sq / n - mean * mean))
    return mean, stddev, mx

# ------------------------------------------------------------ Phase 1: baseline --

print("\n=== BASELINE: keep field of view clear for {} seconds ===".format(BASELINE_SECS))
baseline_vals = []
t_end = time.ticks_add(time.ticks_ms(), BASELINE_SECS * 1000)
while time.ticks_diff(t_end, time.ticks_ms()) > 0:
    mean, stddev, mx = _frame_mean_diff()
    if mean is not None:
        baseline_vals.append(mean)

if len(baseline_vals) < 4:
    print("Not enough baseline frames — try again.")
else:
    n       = len(baseline_vals)
    b_sum   = sum(baseline_vals)
    b_sum2  = sum(v * v for v in baseline_vals)
    b_mean  = b_sum / n
    b_std   = math.sqrt(max(0.0, b_sum2 / n - b_mean * b_mean))
    b_max   = max(baseline_vals)
    suggest = b_mean + 3 * b_std

    print("Baseline ({} frames):".format(n))
    print("  noise mean   = {:.3f}".format(b_mean))
    print("  noise stddev = {:.3f}".format(b_std))
    print("  noise max    = {:.3f}".format(b_max))
    print("  suggested threshold (mean + 3σ) = {:.2f}".format(suggest))
    print("\n=== MONITOR: move through field of view ===")
    print("  frame stats | SNR = mean/noise  z = (mean-noise)/noise_std")

    # --------------------------------------------------------- Phase 2: monitor --
    while True:
        mean, stddev, mx = _frame_mean_diff()
        if mean is None:
            continue
        snr    = mean / b_mean if b_mean > 0 else 0.0
        z      = (mean - b_mean) / b_std if b_std > 0 else 0.0
        marker = "  ***TRIGGER***" if mean > MLX_THRESHOLD else ""
        print("mean={:.2f}  stddev={:.2f}  max={:.2f}  SNR={:.1f}x  z={:.1f}{}".format(
            mean, stddev, mx, snr, z, marker))
