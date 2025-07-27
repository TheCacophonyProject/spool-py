from machine import Pin, I2C
from time import sleep
import pcf8563
import os
import datetime
from util import Buzzer, Clock, RotaryEncoder
from config import *

buzzer = Buzzer()
clock = Clock()
rotary_encoder = RotaryEncoder()

rc1 = Pin(PIN_ROT_ENC_1, Pin.IN, Pin.PULL_UP)
rc2 = Pin(PIN_ROT_ENC_2, Pin.IN, Pin.PULL_UP)
rc4 = Pin(PIN_ROT_ENC_4, Pin.IN, Pin.PULL_UP)
rc8 = Pin(PIN_ROT_ENC_8, Pin.IN, Pin.PULL_UP)

upload_time_file = "upload_time.py"

try:
    os.stat(upload_time_file)
    first_run = True
except OSError:
    first_run = False

# Set to false to skip using the RTC
if True:
    if first_run:
        import upload_time
        print(upload_time)
        clock.write_time(
            seconds=upload_time.seconds, 
            minutes=upload_time.minutes, 
            hours=upload_time.hours, 
            day=upload_time.day_of_week, 
            date=upload_time.date, 
            month=upload_time.month, 
            year=upload_time.year
        )
        os.remove(upload_time_file)
        print("updated the RTC time.")

    if clock.check_low_voltage() != 0:
        buzzer.beep_error(ERROR_TIME_NOT_SET, loop=True)

    #year, month, date, day, hour, minute, second = r.datetime()
    print("RTC time is (UTC): " + str(clock.get_utc_time()))
    print("Local time is :    " + str(clock.get_local_time()))

n = rotary_encoder.position()
print("At position " + str(n))

sleep(1)
for i in range(3):
    buzzer.on()
    sleep(0.1)
    buzzer.off()
    sleep(0.1)
sleep(1)
for i in range(n):
    buzzer.on()
    sleep(0.2)
    buzzer.off()
    sleep(0.2)
sleep(1)
for i in range(3):
    buzzer.on()
    sleep(0.1)
    buzzer.off()
    sleep(0.1)
sleep(1)

filename = "/code{:02d}.py".format(n)
try:
    with open(filename) as f:
        print("running " + filename)
        exec(f.read())
except OSError:
    print(filename + " does not exist!")
    buzzer.beep_error(ERROR_NO_PROGRAM_FOUND, loop=True)
