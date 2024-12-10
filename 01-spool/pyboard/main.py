from machine import Pin, I2C
from time import sleep
import pcf8563
import os
import datetime
from util import Buzzer, Clock
from config import *

buzzer = Buzzer()
clock = Clock()

rc1 = Pin(PIN_ROT_ENC_1, Pin.IN, Pin.PULL_UP)
rc2 = Pin(PIN_ROT_ENC_2, Pin.IN, Pin.PULL_UP)
rc4 = Pin(PIN_ROT_ENC_4, Pin.IN, Pin.PULL_UP)
rc8 = Pin(PIN_ROT_ENC_8, Pin.IN, Pin.PULL_UP)

uploadtimeFile = "uploadtime.py"

try:
    os.stat(uploadtimeFile)
    first_run = True
except OSError:
    first_run = False


# Don't use the RTC for now
if True:
    if first_run:
        import uploadtime
        print(uploadtime)
        clock.write_time(seconds=uploadtime.seconds, minutes=uploadtime.minutes, hours=uploadtime.hours, day=uploadtime.day_of_week, date=uploadtime.date, month=uploadtime.month, year=uploadtime.year)
        os.remove(uploadtimeFile)
        print("updated the RTC time.")


    if clock.check_low_voltage() != 0:
        buzzer.beep_error(ERROR_TIME_NOT_SET, loop=True)

    #year, month, date, day, hour, minute, second = r.datetime()
    print("RTC time is (UTC): " + str(clock.get_utc_time()))
    print("Local time is :    " + str(clock.get_local_time()))

# Calculate position on rotary switch
n = 15 - rc1.value() - 2*rc2.value() - 4*rc4.value() - 8*rc8.value()

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
