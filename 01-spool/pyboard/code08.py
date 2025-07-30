# Program 8 will run through a reset, home, trigger, home cycle.

import time
from util import Spool

spool = Spool()

# It will go through the loop every `loop_time_seconds` amount of seconds. So 120 means 30 loops a hour
loop_time_seconds = 120

while True:
    start_time = time.time() # Get start time in seconds
    
    print("Resetting")
    spool.reset_sequence()
    time.sleep(2)
    
    print("Moving to trigger position.")
    spool.move_to_trigger()
    time.sleep(2)

    print("Moving to home position.")
    spool.move_to_home("ccw")
    time.sleep(2)

    elapsed_time = time.time() - start_time
    if elapsed_time < loop_time_seconds:
        sleep_duration = loop_time_seconds - elapsed_time
        print(f"Sleeping for {sleep_duration} seconds")
        time.sleep(sleep_duration)
    else:
        print("Complete loop in " + str(elapsed_time) + " seconds.")
