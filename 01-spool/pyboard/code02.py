# Program 2 will run the trap triggering from the PIRs when it is enabled through the comms port.
# This is just a simple HIGH for enable and LOW for disable of the trap on the RP2040 Rx pin.

# TODO Testing 

import time
from util import Spool, PIRs, Trap
from machine import Pin

rx_pin = Pin(29, Pin.IN, Pin.PULL_DOWN)


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
    old_state = ""
    while True:
        # Check the state of the enable Pin and PIRs
        if rx_pin.value():
            if pirs.read() == 0:
                state = "active, no pir movement"
            else:
                print("active and pir movement")
                break
        else:
            if pirs.read() == 0:
                state = "not active, no pir movement"
            else:
                state = "not active, pir movement"

        # Print state if it has changed
        if old_state != state:
            print(state)
            old_state = state

        # Small sleep
        time.sleep(0.05)
    
    print("Motion detected, moving to trigger position.")
    spool.move_to_trigger()
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home("ccw")
    
    print("Waiting 10 minutes until resetting")
    time.sleep(10*60)
