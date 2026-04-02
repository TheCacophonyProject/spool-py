# Program 4: trigger the trap from PIRs, enabled/disabled via UART.

import time
from util import Spool, PIRs, RPi_UART
from machine import Pin, I2C
from config import *

i2c = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))

pirs = PIRs(i2c)
uart = RPi_UART(baudrate=9600)
spool = Spool(i2c, uart=uart)

# variables that can be read/set using "read" and "write"
vars = {
    "enable": False,
    "trigger": False,
}

def reset_spool(data):
    spool.reset_sequence()
    return "", True

def trigger_spool(data):
    if not spool.at_home():
        spool.move_to_home()
    spool.release()
    return "", True

def read_pirs(data):
    return pirs.read(), True

def read_spool(data):
    return spool.read(), True

commands = {
    "reset_spool": reset_spool,
    "trigger_spool": trigger_spool,
    "read_pirs": read_pirs,
    "read_spool": read_spool,
}

def handle_uart():
    request = uart.check_for_message()
    if request is None:
        return
    if request.type == "write":
        var = request.data.get('var')
        if var in vars:
            vars[var] = request.data.get('val')
            uart.send_ack(request.id)
        else:
            uart.send_nack(request.id)
    else:
        print("Unknown request: " + str(request))
        uart.send_nack(request.id)

def sleep_handling_uart(seconds):
    end = time.time() + seconds
    while time.time() < end:
        handle_uart()
        time.sleep(0.01)

print("Waiting for PIRs to detect motion while enabled...")

old_state = ""

print("Resetting")
spool.reset_sequence()
time.sleep(2)

print("Moving to home position.")
spool.move_to_home()
time.sleep(2)

while True:
    handle_uart()

    # Check PIRs only when enabled
    if vars["enable"]:
        if pirs.read() == 0:
            state = "active, no motion"
        else:
            state = "active, motion"
            vars["trigger"] = True
    else:
        if pirs.read() == 0:
            state = "inactive, no motion"
        else:
            state = "inactive, motion"

    if state != old_state:
        print(state)
        old_state = state
        uart.send({"type": "stateChange", "data": state})
    
    if vars["trigger"]:
        vars["trigger"] = False
        print("Triggering spool...")
        spool.release()
        sleep_handling_uart(2)

        print("Waiting 10 minutes until resetting")
        sleep_handling_uart(10*60)
        old_state = ""

    time.sleep(0.01)
