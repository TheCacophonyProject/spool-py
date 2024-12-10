# Program 1 will run the trap triggering from the PIRs. Can be set to only trigger at night.
import time
from util import Spool, PIRs

spool = Spool()
pirs = PIRs()

while True:
    start_time = time.time() # Get start time in seconds
    
    print("Moving to reset")
    spool.move_to_reset()
    time.sleep(2)
    
    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)

    print("Waiting for PIRs to detect motion.")
    while pirs.read() == 0:
        pass
    print("PIRs Detected motion.")

    print("Moving to trigger position.")
    spool.move_to_trigger()
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)

    #elapsed_time = time.time() - start_time
    #if elapsed_time < 60:
    #    time.sleep(60 - elapsed_time)
