# Program 2 will run the trap triggering from the PIRs when it is enabled through the comms port.
# This is just a simple HIGH for enable and LOW for disable of the trap on the RP2040 Rx pin.

# TODO Testing 

import time
from util import Spool, PIRs, Trap

spool = Spool()
pirs = PIRs()
trap = Trap()

while True:
    print("Resetting")
    spool.reset_sequence()
    time.sleep(2)
    
    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)

    print("Waiting for PIRs to detect motion and enabled to trigger.")
    while pirs.read() == 0 and trap.enabled:
        pass
    
    spool.move_to_trigger()
    print("Motion detected.")
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)
