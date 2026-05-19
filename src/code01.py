# Program 1 will run the trap triggering from the PIRs. Can be set to only trigger at night.

import time
from util import Spool, PIRs, Clock
from user_config import *

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
    enabled = spool.is_enabled()

    # Check what new state we are in.
    if motion:
        # TODO: Make motion event, need to throttle making this event.
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
