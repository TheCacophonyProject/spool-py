import pcf8563
import timezone
import datetime
from machine import I2C, UART, Pin, PWM, reset
from config import *
from user_config import *
import time
from ina219 import INA219

MAX_U16 = 65535


class Spool:
    def __init__(self, i2c):
        # H-Bridge driver pins, set frequency and set to 0
        self.h_in1 = PWM(Pin(PIN_H_IN_1), freq=20000)
        self.h_in1.duty_u16(0)
        self.h_in2 = PWM(Pin(PIN_H_IN_2), freq=20000)
        self.h_in2.duty_u16(0)
        self.direction = "stop"

        # Photointerrupter pins, set power to off.
        self.en_photo_interrupter = Pin(PIN_EN_PHOTO_INTERRUPTER, Pin.OUT)
        self.en_photo_interrupter.on() # TODO: Add logic around this so it can be turned off when it is not needed.
        self.photo_interrupter_home = Pin(PIN_PHOTO_INTERRUPTER_HOME, Pin.IN)
        self.photo_interrupter_reset = Pin(PIN_PHOTO_INTERRUPTER_RESET, Pin.IN)

        # Electromagnet pins, set to off
        self.electromagnet_en_pin = Pin(PIN_ELECTROMAGNET_RELEASE, Pin.OUT)
        self.electromagnet_en_pin.off()

        # First guess for reset duration.
        self.home_to_reset_duration = HOME_TO_RESET_DURATION

        # Current sensor
        self.ina219 = INA219(SHUNT_OHMS, i2c)
        self.ina219.configure(gain = INA219.GAIN_8_320MV)

        # Buzzer
        self.buzzer = Buzzer()

    def stop(self):
        # Writing both values to high will set the motor driver into "break/stop" mode.
        self.h_in1.duty_u16(MAX_U16)
        self.h_in2.duty_u16(MAX_U16)
        self.speed = 0
        self.direction = "stop"
        # TODO: After we have stopped we might want to switch into LOW, LOW instead
        # of HIGH, HIGH so the motor driver will go into a sleep mode to save power.

    # _drive_cw is towards reset
    def _drive_cw(self, speed=100):
        if self.at_reset():
            self.stop()
            return
        if self.direction == "cw" and self.speed == speed:
            # Nothing to do here. Don't set the duty cycle again, 
            # setting it multiple times in quick succession can have a bad affect
            return
        self.h_in1.duty_u16(int(speed * MAX_U16 / 100))
        self.h_in2.duty_u16(0)
        self.speed = speed
        self.direction = "cw"

    # _drive_ccw is towards home
    def _drive_ccw(self, speed=100):
        if self.at_home():
            self.stop()
            return
        if self.direction == "ccw" and self.speed == speed:
            # Nothing to do here. Don't set the duty cycle again, 
            # setting it multiple times in quick succession can have a bad affect
            return
        self.h_in2.duty_u16(int(speed * MAX_U16 / 100))
        self.h_in1.duty_u16(0)
        self.speed = speed
        self.direction = "ccw"

    def at_home(self):
        return self.photo_interrupter_home.value() == 1

    def at_reset(self):
        return self.photo_interrupter_reset.value() == 1

    def reset_sequence(self, steps=4):
        print("======== Running reset sequence ========")
        # Stop and then move to home to start the reset sequence.
        self.stop()
        time.sleep(0.2)
        self.move_to_home()
        time.sleep(1)

        # For the reset sequence rather than making it move directly to reset we make multiple 
        # "steps", each time returning back to home and then moving further next time.
        # This is to help clear out the blinds of dirt and such.
        step_size = self.home_to_reset_duration/steps
        steps = steps -1 # -1 because we always do the last step (to reset)
        for i in range(steps):
            sleep_duration = step_size*(i+1)
            self.move_to_reset(timeout=sleep_duration, timeout_error=False)
            time.sleep(0.5)
            self.move_to_home()
            time.sleep(0.5)
            
        # TODO, put a time limit on this as to not burn out the motor if it takes too long
        start_time = time.time()
        self.move_to_reset()
        self.home_to_reset_duration = time.time() - start_time  # Update how long it takes to move from home to reset
        print("home_to_reset_duration", self.home_to_reset_duration)
        time.sleep(0.5)
        self.move_to_home()
        time.sleep(0.5)
        print("Finished reset sequence =================")


    def move_to_reset(self, timeout=15, timeout_error=True):
        print("Moving to reset")
        if self.at_reset():
            print("Already at reset")
            return True
        self._drive_cw()
        return self._wait_to_stop_spool(self.at_reset, timeout, timeout_error)
    
    def move_to_home(self, timeout=15, timeout_error=True):
        print("Moving to home")
        if self.at_home():
            print("Already at home")
            return True
        self._drive_ccw()
        return self._wait_to_stop_spool(self.at_home, timeout, timeout_error)

    def release(self):
        # It is only safe to trigger the trap if the spool has made it back to the home position.
        if not self.at_home():
            return False
        
        # At home position so it is safe to release the trap.
        self.electromagnet_en_pin.on()
        time.sleep(0.5)
        self.electromagnet_en_pin.off()
        return True
        

    def _wait_to_stop_spool(self, checker_function, timeout, error_on_timeout):
        start_time = time.time()
        self.ina219.wake()
        avg = RingAvg(30)
        max_avg_current = 0
        max_current = 0
        while True:
            # Check if it has got to the target
            if checker_function():
                self.stop()
                print("Finished move. Reason: Got to target")
                self.ina219.sleep()
                print("Max current ", max_current)
                print("Max average current ", max_avg_current)
                return True

            # Timeout on moving.
            if time.time() - start_time > timeout:
                self.stop()
                print("Finished move. Reason: Timed out")
                if error_on_timeout:
                    self.buzzer.beep_error(ERROR_MOVEMENT_TIMEOUT)
                self.ina219.sleep()
                return False
            
            try:
                current = self.ina219.current()
                if current > max_current:
                    max_current = current
                avg.add(abs(current))
                avg_current = avg.avg()
                if avg_current > max_avg_current:
                    max_avg_current = avg_current
            except Exception as e:
                print("ina error", e)
            if avg.avg() > MAX_CURRENT:
                self.stop()
                print("Finished move. Reason: Over current")
                # TODO, work out how we will handle this case
                self.buzzer.beep_error(ERROR_OVER_CURRENT)
                self.ina219.sleep()
                return False

class RingAvg:
    def __init__(self, size):
        assert size > 0
        self.size = size
        self.buf = [0.0] * size   # preallocate (use array('f') if you like)
        self.sum = 0.0
        self.count = 0            # how many valid samples (<= n)
        self.idx = 0              # next write index

    def add(self, x):
        x = float(x)
        if self.count < self.size:
            # still filling
            self.buf[self.idx] = x
            self.sum += x
            self.count += 1
        else:
            # overwrite oldest
            old = self.buf[self.idx]
            self.buf[self.idx] = x
            self.sum += x - old
        self.idx += 1
        if self.idx == self.size:    # faster than % in many ports
            self.idx = 0

    def avg(self):
        return self.sum / self.size

class Buzzer:
    def __init__(self):
        self.pwm_instance = PWM(Pin(PIN_BUZZER))
        self.off()

    def on(self):
        self.pwm(1000, 50)

    def off(self):
        self.pwm(1000, 0)

    def pwm(self, freq, duty):
        self.pwm_instance.freq(freq)
        self.pwm_instance.duty_u16(int(duty * MAX_U16 / 100))

    def beep_trap_ready(self):
        for i in range(5):
            time.sleep(0.5)
            self.on()
            time.sleep(0.5)
            self.off()
        print("Trap is ready.")

    def beep_error(self, beeps):
        for _ in range(3):
            for _ in range(3):
                self.on()
                time.sleep(0.2)
                self.pwm(800, 50)
                time.sleep(0.2)
            self.off()
            time.sleep(1)
            for i in range(beeps):
                self.on()
                time.sleep(0.2)
                self.off()
                time.sleep(0.2)
            time.sleep(1)
        reset()

class RotaryEncoder:
    def __init__(self):
        self.pin_1 = Pin(PIN_ROT_ENC_1, Pin.IN, Pin.PULL_UP)
        self.pin_2 = Pin(PIN_ROT_ENC_2, Pin.IN, Pin.PULL_UP)
        self.pin_4 = Pin(PIN_ROT_ENC_4, Pin.IN, Pin.PULL_UP)
        self.pin_8 = Pin(PIN_ROT_ENC_8, Pin.IN, Pin.PULL_UP)

    def position(self):
        return 15 - self.pin_1.value() - 2*self.pin_2.value() - 4*self.pin_4.value() - 8*self.pin_8.value()

class Clock:
    def __init__(self, i2c):
        self.r = pcf8563.PCF8563(i2c)
        self.latitude = LATITUDE
        self.longitude = LONGITUDE
        dst = timezone.time_change_rule(-1, 6, 9, 2, 780)
        st = timezone.time_change_rule(0, 6, 4, 2, 720)
        self.nz_tz = timezone.timezone(dst, st)
        self.night_only = Pin(PIN_SW_NIGHT_ONLY, Pin.IN, Pin.PULL_UP)

    def get_local_time(self, utc_time=None):
        if utc_time is None:
            utc_time = self.get_utc_time()
        return self.nz_tz.get_local_time(utc_time)

    def write_time(self, **kwargs):
        self.r.write_all(**kwargs)

    def get_utc_time(self):
        year, month, date, day, hour, minute, second = self.r.datetime()
        return datetime.datetime(
            year=year + 2000,
            month=month,
            day=date,
            hour=hour,
            minute=minute,
            second=second,
        )

    def is_night(self):
        utc = self.get_utc_time()
        local_time = self.get_local_time(utc)
        tz = self.nz_tz.get_current_tz(utc).timezone
        sunrise = timezone.get_sunrise(utc, LATITUDE, LONGITUDE, tz)
        sunset = timezone.get_sunset(utc, LATITUDE, LONGITUDE, tz)
        return local_time.time() < sunrise or sunset < local_time.time()

    def in_active_window(self):
        # If night time mode is enabled check if it is night, else return true.
        if self.night_only.value() == 1:
            return self.is_night()
        return True

    def check_low_voltage(self):
        return self.r.check_low_voltage()

class PIRs:
    def __init__(self, i2c):
        self.i2c = i2c
        self.pir_1 = Pin(PIN_PIR_1, Pin.IN)
        self.pir_2 = Pin(PIN_PIR_2, Pin.IN)
        self.set_pir_sensitivity(PIR_SENSITIVITY)

    def read(self):
        return self.pir_1.value() or self.pir_2.value()

    def read_sensitivity(self):
        return self.pir_sensitivity.read()

    def set_pir_sensitivity(self, value):
        value = 127 - value
        bytearray(0) + bytearray([value])
        if value >= 128:
            value = 128
        if value < 0:
            value = 0
        # Writing to a programmable POT as a way to set the sensitivity for the PIRs
        self.i2c.writeto(0x3E, bytes([0, value]))

class RPi_UART:
    def __init__(self):
        self.uart = UART(0, baudrate=9600, tx=Pin(PIN_UART_TX), rx=Pin(PIN_UART_RX))

    def check_for_message(self):
        # Check to see if there is any data in the UART buffer, if not return None
        if not self.uart.any():
            return None
        
        # There is some data so lets read the full line.
        # TODO: Timeout of reading the whole line
        line = bytearray()
        while True:
            if self.uart.any():
                char = self.uart.read(1)
                if char == b"\n":
                    break
                line.extend(char)
        
        data = line.decode('utf-8')
        
        # Check that we get the message in the correct format "<message|checksum>"
        if not(data.startswith('<') and '|' in data and data.endswith('>')):
            self.send({"response": "NACK", "error": "Invalid message format"})
            return None
        
        # Split out message and check the checksum
        message_raw, checksum = data[1:-1].split('|') # TODO, split at last | in case there is one in the message.
        if self._compute_checksum(message_raw.encode()) != int(checksum):
            self.send({"response": "NACK", "error": "Checksum mismatch"})
            return None
        
        # Load the message as a json and return
        try:
            message_json = ujson.loads(message_raw)
        except Exception as e:
            self.send({"response": "NACK", "error": "Parsing error"})
            return None

        # Turn the json into a Request object and return
        return Request(message_json)

    def send(self, data):
        json_str = ujson.dumps(data)
        checksum = self._compute_checksum(json_str.encode())
        uart.write('<{}|{}>'.format(json_str, checksum))  

    def _compute_checksum(self, message):
        return sum(message) % 256

    def send_nack(self, message_id=0):
        self.send({
            "id": id,
            "response": True,
            "type": "NACK",
            "data": ""
        })
    
    def send_ack(self, message_id=0):
        self.send({
            "id": id,
            "response": True,
            "type": "ACK",
            "data": ""
        })

class Request():
    def __init__(self, json):
        self.id = json.get('id')
        self.response = json.get('response')
        self.type = json.get('type')
        self.data = ujson.loads(json.get('data'))
        print("new request, id: {}, response: {}, type: {}, data: {}".format(self.id, self.response, self.type, self.data))
        
    def run(self):
        if self.type == "write":
            write_read_data[self.data.get('var')] = self.data.get('val')
            print(write_read_data)
            send_response(ack_message(self.id))
            return
        if self.type == "read":
            send_response({
                "id": id,
                "response": True,
                "type": "read",
                "data": {self.data.get('var'): write_read_data[self.data.get('var')]}
            })
            return
        
        if self.type == "command":
            command = actions[self.data.get('command')]
            #TODO add params
            if command:
                send_response(ack_message(self.id))
                command()
            else:
                send_response(nack_message(self.id))
            return

        send_response(nack_message(self.id))
