# Program 1 will run the trap triggering from the PIRs. Can be set to only trigger at night.

import time
from util import Spool, PIRs

spool = Spool()
pirs = PIRs()
clock = Clock()

while True:
    print("Resetting")
    spool.reset_sequence()
    time.sleep(2)
    
    print("Moving to home position.")
    spool.move_to_home("cw")
    time.sleep(2)

    print("Waiting for PIRs to detect motion during the active window.")
    while not clock.in_active_window() or pirs.read() == 0:
        time.sleep(0.05)
        pass
    
    spool.move_to_trigger()
    print("Motion detected.")
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home("ccw")
    
    print("Waiting 10 minutes until resetting")
    time.sleep(10*60)
