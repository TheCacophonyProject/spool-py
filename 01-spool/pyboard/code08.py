# Program 8 will run through a reset, home, trigger, home cycle every minutes.

import time
from util import Spool

spool = Spool()

# Initialize the spool. This will drive around to trigger position
#spool.init()

while True:
    start_time = time.time() # Get start time in seconds
    
    print("Moving to reset")
    spool.reset_sequence()
    time.sleep(2)
    
    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)
    
    print("Moving to trigger position.")
    spool.move_to_trigger()
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home()
    time.sleep(2)

    elapsed_time = time.time() - start_time
    if elapsed_time < 60:
        time.sleep(60 - elapsed_time)
