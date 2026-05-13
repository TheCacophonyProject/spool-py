# Program 7 will play different noises depending on what PIRs are active. 
# Short beeps for PIR1 and long beeps for PIR2, and constant tone for both active.
# The encoder can be moved from position 0 for the lowest sensitivity to position 9 for the highest.
# If setting the sensitivity by the encoder you need to make the PIR switch is set to software not manual.

from util import PIRs, Buzzer
import time
import as5600

pirs = PIRs()
buzzer = Buzzer()

while True:
    pir1 = pirs.pir_1.value()
    pir2 = pirs.pir_2.value()
    if pir1 and pir2:
        buzzer.pwm(1800, 50)
    elif pir1:
        buzzer.pwm(800, 20)
    elif pir2:
        buzzer.pwm(1200, 20)
    else:
        buzzer.off()
    
    time.sleep(0.02)

