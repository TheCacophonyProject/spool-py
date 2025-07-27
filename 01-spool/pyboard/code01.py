# Program 1 will run the trap triggering from the PIRs. Can be set to only trigger at night.

# TODO Make it only trigger at night.
# TODO Testing

import time
from util import Spool, PIRs

trigger_window = TriggerWindow()

spool = Spool()
pirs = PIRs()
clock = Clock()

while True:
    print("Resetting")
    spool.reset_sequence()
    time.sleep(2)
    
    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)

    print("Waiting for PIRs to detect motion.")
    while pirs.read() == 0:
        pass
    
    spool.move_to_trigger()
    print("Motion detected.")
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)
