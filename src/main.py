from machine import Pin, I2C
import machine
from time import sleep
import pcf8563
import os
import sys
import io
import datetime
from util import Buzzer, Clock, RotaryEncoder, RPi_UART, Message
from config import *

i2c = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))

buzzer = Buzzer()
clock = Clock(i2c)
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
        # TODO: Send error message here
        buzzer.beep_error(ERROR_TIME_NOT_SET)

    #year, month, date, day, hour, minute, second = r.datetime()
    print("RTC time is (UTC): " + str(clock.get_utc_time()))
    print("Local time is :    " + str(clock.get_local_time()))
    # buzzer.on()
    # sleep(1)
    # buzzer.off()
    # sleep(1)
    # machine.reset()

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

def uart_one_message(message: Message):
    uart = None
    try:
        uart = RPi_UART(None)
        uart.send_message(message)
    except Exception as err:
        print(get_err_str(err))
        print("Error when trying to send message via UART")
    finally:
        if uart is not None:
            uart.close()

def get_err_str(err):
    buf = io.StringIO()
    sys.print_exception(err, buf)
    return buf.getvalue()

def save_error(err):
    try:
        # Check if there is enough space to save the error
        stat = os.statvfs("/")
        free_bytes = stat[0] * stat[3]
        print("Free bytes: " + str(free_bytes))
        if free_bytes < 100_000:
            print("Not enough space to save error.log")
            return
        # Save the error with the timestamp
        timestamp = str(clock.get_utc_time())
        with open("error.log", "a") as f:
            f.write("--- " + timestamp + " ---\n")
            f.write(get_err_str(err))
            f.write("\n")
        print("Error saved to error.log")

    except Exception:
        print("Error when trying to save to error.log")

while True:

    # Check if the program file exists.
    try:
        os.stat(filename)
    except OSError:
        print(filename + " not found")
        uart_one_message(Message(0, "ERROR", filename + " not found"))
        uart.close()
        buzzer.beep_error(ERROR_NO_PROGRAM_FOUND)
        sleep(10)
        continue

    # Run the program.
    try:
        with open(filename) as f:
            print("running " + filename)
            uart_one_message(Message(0, "RUNNING", filename))
            exec(f.read())
    except Exception as e:
        print("Runtime error: " + get_err_str(e) + "\n")
        # We want to send the error via UART but it is often not available
        # as it is was in use by the program. So we save the error to a file
        # and sent it when starting up next.
        uart_one_message(Message(0, "ERROR", get_err_str(e)))
        save_error(e)
        
        buzzer.beep_error(ERROR_RUNTIME_ERROR)
    sleep(60)
    machine.reset()
