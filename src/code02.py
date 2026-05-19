# Program 2 will run the trap triggering from the PIRs when it is enabled through the comms port.
# This is just a simple HIGH for enable and LOW for disable of the trap on the RP2040 Rx pin.

# TODO Testing 

import time
from util import *
from machine import Pin

import time
from util import Spool, PIRs, Clock
from user_config import *

rx_pin = Pin(29, Pin.IN, Pin.PULL_DOWN)
spool = Spool()
pirs = PIRs()

print("Resetting")
spool.reset_sequence()
time.sleep(2)

print("Waiting for PIRs to detect motion while the trap is active.")
old_state = ""

while True:
    # Take reading to determine state
    motion = not pirs.read() == 0
    enabled = rx_pin.value() == 1

    # Check what new state we are in.
    if motion:
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