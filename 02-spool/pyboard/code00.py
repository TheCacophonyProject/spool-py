# Program 0 is used for debugging

from util import *
import time

i2c = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))

pirs = PIRs(i2c)
uart = RPi_UART(baudrate=9600)
spool = Spool(i2c)

# variables that can be read/set using "read" and "write"
vars = {
    "enabled": False # If the trap is active or not, will it trigger with motion detected or not.
}

# These are the command handlers, they should return a tuple of (data, success). 
# The data should be in the format of a JSON.
# The success should be a bool of whether the command was successful or not.

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

def set_time(data):
    return "", True

# Commands that can be triggered. Will return the result of the command.
commands = {
    "reset_spool": reset_spool,
    "trigger_spool": trigger_spool,
    "read_pirs": read_pirs,
    "read_spool": read_spool,
    "set_time": set_time,
}

print("Waiting for commandss...")

uart.send({"type": "ping"})

while True:
    request = uart.check_for_message()
    if request is not None:
        print(request)
        # Handle "command" requests.
        if request.type == "command":
            command = request.data.get('command')

            if command in commands:
                data, success = commands[command](request.data)
                if success:
                    uart.send_ack(request.id, data)
                else:
                    uart.send_nack(request.id)
            else:
                uart.send_nack(request.id)

        elif request.type == "read":
            var = request.data.get('var')
            if var in vars:
                uart.send_ack(request.id, str(vars[var]))
            else:
                uart.send_nack(request.id)

        elif request.type == "write":
            var = request.data.get('var')
            if var in vars:
                vars[var] = request.data.get('val')
                uart.send_ack(request.id)
            else:
                uart.send_nack(request.id)
