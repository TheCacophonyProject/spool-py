from util import *
import time

pirs = PIRs()
uart = RPi_UART()
spool = Spool()

# State of the trap. Use "read" and "write" to access.
state = {
    "trap_active": False # If the trap is active or not, will it trigger with motion detected or not.
}

# Commands that can be triggered. Will return the result of the command.


# These are the command handlers, they should return a tuple of (data, success). 
# The data should be in the format of a JSON.
# The success should be a bool of whether the command was successful or not.

def reset_spool(data):
    spool.reset_sequence()
    return True

def trigger_spool(data):
    if not spool.at_home():
        spool.move_to_home()
    spool.release()
    return True

def read_pirs(data):
    return pirs.read()

def read_spool(data):
    return spool.read()

def set_time(data):
    return True

commands = {
    "reset_spool": reset_spool,
    "trigger_spool": trigger_spool,
    "read_pirs": read_pirs,
    "read_spool": read_spool,
    "set_time": set_time,
}

print("Waiting for commands...")

while True:
    request = uart.check_for_message()
    if request is not None:
        
        # Handle "command" requests.
        if request.type == "command":
            command = request.data.get('command')

            if command in commands:
                data, success = commands[command](request.data)
                if success:
                    uart.send_ack(request.id, data)
                else:
                    uart.send_nack(request.id)

    time.sleep(0.02)
