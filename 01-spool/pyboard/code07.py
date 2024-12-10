# Program 7 will play different noises depending on what PIRs are active. 
# Short beeps for PIR1 and long beeps for PIR2, and constant tone for both active.
# The encoder can be moved from position 0 for the lowest sensitivity to position 9 for the highest.
# If setting the sensitivity by the encoder you need to make the PIR switch is set to software not manual.

from util import PIRs
import time
import as5600

pirs = PIRs()
buzzer = Buzzer()

while True:
    if pirs.read() == 0:
        #print("No motion detected.")
        buzzer.off()
    else:
        #print("Motion detected.")
        buzzer.on()
    
    #print(pir.read_sensitivity())
    time.sleep(0.02)

