# Program 1 will run the trap triggering from the PIRs. Can be set to only trigger at night.

import time
from util import Spool, PIRs, Clock

i2c = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))

spool = Spool(i2c)
pirs = PIRs(i2c)
clock = Clock(i2c)

while True:
    print("Resetting")
    spool.reset_sequence()
    time.sleep(2)
    
    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)

    print("Waiting for PIRs to detect motion during the active window.")
    old_state = ""
    while True:
        # Check the state of the clock and PIRs
        if clock.in_active_window():
            if pirs.read() == 0:
                state = "active, no motion"
            else:
                print("active and motion detected")
                break
        else:
            if pirs.read() == 0:
                state = "inactive, no motion"
            else:
                state = "inactive, motion"

        # Only print the state if it has changed
        if state != old_state:
            print(state)
            old_state = state

        # Wait a bit
        time.sleep(0.01)
    
    print("Motion detected, releasing spool.")
    spool.release()
    time.sleep(2)
    
    print("Waiting 10 minutes until resetting")
    time.sleep(10*60)
