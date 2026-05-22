# Program 1 will run the trap triggering from the APIRs.

import time
from util import Spool, PIRs, RPi_UART, motion_message, SharedDict, Clock, Switches, APIR
from user_config import *

shared_dict = SharedDict()
rpi_uart = RPi_UART(shared_dict)
spool = Spool(rpi_uart=rpi_uart)
apirs = APIR()
clock = Clock()
switches = Switches()

print("Resetting")
spool.reset_sequence()
time.sleep(2)

print("Waiting for APIRs to detect motion while the trap is active.")
old_state = ""

last_motion_message = -10
motion_message_gap = 30 # Minimum time between motion messages
old_enabled = False

enabled_checks = [
    spool.enable_check,        # Check that the spool is at the home position
    clock.enable_check,        # Check that it can trigger at the current time
    # shared_dict.enable_check,  # Check that the camera hasn't told it to be disabled
    switches.enable_check,     # Check that the switches shouldn't disable the trap
]

def check_checks(enable_checks):
    failed_reasons = []
    all_passed = True
    for check in enable_checks:
        check_passed, reason = check()
        if not check_passed:
            all_passed = False
            failed_reasons.append(reason)
    return all_passed, ', '.join(failed_reasons)

old_failed_check_reasons = ""

while True:
    # Take reading to determine state
    motion = apirs.motion()

    enabled, failed_check_reasons = check_checks(enabled_checks)
    if failed_check_reasons != old_failed_check_reasons:
        old_failed_check_reasons = failed_check_reasons
        rpi_uart.send_message(Message(0, "DISABLE_REASONS", failed_check_reasons))

    if old_enabled != enabled:
        if enabled:
            rpi_uart.send_message(Message(0, "ENABLED"))
        else:
            rpi_uart.send_message(Message(0, "DISABLED"))
        old_enabled = enabled

    # Check what new state we are in.
    if motion:
        # Send a motion message if one hasn't been sent in the last 10 seconds
        now = time.time()
        if last_motion_message + motion_message_gap < now:
            print("Sending motion message")
            rpi_uart.send_message(motion_message())
            last_motion_message = now

        if enabled:
            print("Motion detected, releasing spool.")
            spool.release()
            print(f"Waiting {SPOOL_RESET_DELAY_MINUTES} minutes until resetting.")
            time.sleep(SPOOL_RESET_DELAY_MINUTES * 60)
            print("Resetting")
            spool.reset_sequence()
            print("Waiting one minute before activating trap again.")
            time.sleep(60)
            new_state = "Trap is reset"
        else:
            new_state = "Motion detected and not enabled, not releasing spool."
    else:
        if enabled:
            new_state = "No motion detected and enabled, not releasing spool."
        else:
            new_state = "No motion detected and not enabled, not releasing spool."

    # Only print the state if it has changed
    if new_state != old_state:
        print(new_state)
        old_state = new_state

    # Wait a bit between loops
    time.sleep(0.01)
