# Program 0 the  spool can be moved manually to different positions depending on what position
# the encoder is at. 0 is the home position. 9 is the trigger position. 8 is the reset position.
# 1 to 7 are the intermediate positions between home and reset.


#     Trigger    Reset
#   Home \     /
#       \  9   0
#        8       1
#       7         2
#        6       3
#          5   4


# TODO Testing

import time
from util import Spool, RotaryEncoder

rotary_encoder = RotaryEncoder()
spool = Spool()

encoder_val = rotary_encoder.position()

while True:
    # Wait until new encoder value is stable for 2 seconds
    t = time.time()
    while time.time() - t < 2:
        new_encoder_val = rotary_encoder.position()
        if new_encoder_val != encoder_val:
            encoder_val = new_encoder_val
            t = time.time()
        time.sleep(0.2)
        print(new_encoder_val)
        print(spool.get_angle())

    print(encoder_val)
    if encoder_val == 0:
        spool.move_to_reset()
    elif encoder_val == 9:
        spool.move_to_trigger()
    elif encoder_val == 8:
        spool.move_to_home()
    
    else:
        angle = spool.reset_angle - (spool.reset_angle - spool.home_angle) / 8 * (encoder_val) 
        print(angle)
        if abs(spool.get_angle() - angle) > 4:
            spool.move_to_angle(angle)
            time.sleep(1)

