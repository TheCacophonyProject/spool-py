import pcf8563
import timezone
import datetime
from machine import I2C, UART, Pin, PWM, ADC
from config import *
from time import sleep
import time
from as5600 import AS5600

i2c = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))




class Spool:
    def __init__(self):  # , as5600):
        # H-Bridge driver pins
        self.h_in1 = PWM(Pin(PIN_H_IN_1), freq=20000)
        self.h_in1.duty_u16(0)
        self.h_in2 = PWM(Pin(PIN_H_IN_2), freq=20000)
        self.h_in2.duty_u16(0)
        self.direction = "stop"
        self.speed = 0

        # Photointerrupter pins
        self.en_photo_interrupter = Pin(PIN_EN_PHOTO_INTERRUPTER, Pin.OUT)

        self.photo_interrupter_home = Pin(PIN_PHOTO_INTERRUPTER_HOME, Pin.IN)
        self.photo_interrupter_trigger = Pin(PIN_PHOTO_INTERRUPTER_TRIGGER, Pin.IN)
        self.photo_interrupter_reset = Pin(PIN_PHOTO_INTERRUPTER_RESET, Pin.IN)

        # Power up photointerrupters
        self.en_photo_interrupter.value(1)
        #self.angle_offset = 0
        #self.find_angle()

        self.home_to_reset_duration = 10

        # TODO
        # Setup timers for stopping motor 

    def set_angle_zero(self):
        self.angle_offset = self._angle_0_360() - 8

    def stop(self):
        self.h_in1.duty_u16(65536)
        self.h_in2.duty_u16(65536)
        self.speed = 0
        self.direction = "stop"

    # _drive_cw is towards trigger
    def _drive_cw(self, speed=100):
        if self.at_trigger():
            self.stop()
            return
        if self.direction == "cw" and self.speed == speed:
            # Nothing to do here. Don't set the duty cycle again.
            return
        self.h_in1.duty_u16(int(speed * 65536 / 100))
        self.h_in2.duty_u16(0)
        self.speed = speed
        self.direction = "cw"

    # _drive_ccw is towards reset
    def _drive_ccw(self, speed=100):
        if self.at_reset():
            self.stop()
            return
        if self.direction == "ccw" and self.speed == speed:
            # Nothing to do here. Don't set the duty cycle again.
            return
        self.h_in1.duty_u16(0)
        self.h_in2.duty_u16(int(speed * 65536 / 100))
        self.speed = speed
        self.direction = "ccw"

    def at_home(self):
        return self.photo_interrupter_home.value() == 1

    def at_reset(self):
        return self.photo_interrupter_reset.value() == 1

    def at_trigger(self):
        return self.photo_interrupter_trigger.value() == 1

    def move_to_reset(self):
        print("Moving to reset")
        self._drive_ccw()
        while not self.at_reset():
            continue
        self.stop()
        print("Got to reset position, ")

    def move_to_trigger(self):
        print("Moving to trigger")
        self._drive_cw()
        while not self.at_trigger():
            continue
        self.stop()
        print("Got to trigger position")
        print()

    def move_to_angle(self, angle):
        print("Moving to angle", angle)
        print("starting at angle", self.get_angle())
        if angle > self.get_angle():
            self._drive_ccw()
            while angle >= self.get_angle():
                #print(self.get_angle())
                continue
        else:
            self._drive_cw()
            while angle <= self.get_angle():
                #print(self.get_angle())
                continue
        self.stop()
        print("Got to angle", angle, self.get_angle())

    def reset_sequence(self, steps=4):
        print("Running reset sequence =================")
        self.stop()
        time.sleep(0.2)
        self.move_to_home("cw")
        time.sleep(1)

        step_size = self.home_to_reset_duration/steps
        steps = steps -1 # -1 because we always do the last step (to reset)
        for i in range(steps):
            sleep_duration = step_size*(i+1)
            self._drive_ccw() # Towards reset
            time.sleep(sleep_duration)
            self.stop()
            time.sleep(0.5)
            self.move_to_home("cw")
            time.sleep(0.5)
            
        # TODO, put a time limit on this as to not burn out the motor if it takes too long
        start_time = time.time()
        self.move_to_reset()
        self.home_to_reset_duration = time.time() - start_time  # Update how long it takes to move from home to reset
        print("home_to_reset_duration", self.home_to_reset_duration)
        time.sleep(0.5)
        self.move_to_home("cw")
        time.sleep(0.5)
        print("Finished reset sequence =================")

    def reset_sequence_old(self, steps=4):
        print("Running reset sequence =================")
        self.move_to_home()
        time.sleep(1)

        step_size = (self.reset_angle - self.home_angle)/steps
        steps = steps -1 # -1 because we always do the last step (to reset)
        for i in range(steps):
            target_degrees = self.home_angle + (i+1)*step_size
            self.move_to_angle(target_degrees)
            time.sleep(1)
            self.move_to_home()
            time.sleep(1)
        
        self.move_to_reset()
        time.sleep(1)
        self.move_to_home()
        time.sleep(1)
        print("Finished reset sequence =================")

    def move_to_home(self, direction):
        print("Moving to home")
        #if self.home_angle is None:
        #    self.find_angle()

        #if self.get_angle() < self.home_angle:
        #    self._drive_ccw()
        #    ccw = True
        if direction == "ccw":
            self._drive_ccw()
            ccw = True
        elif direction == "cw":
            self._drive_cw()
            ccw = False
        else:
            raise Exception("Invalid direction")
        while not self.at_home():
            if ccw:
                if self.at_reset():
                    self.stop()
                    print("Missed the home position....")
                    ## TODO Make some sort of alert as this should not have happened
                    return
            else:
                if self.at_trigger():
                    self.stop()
                    print("Missed the home position....")
                    ## TODO Make some sort of alert as this should not have happened
                    return
            continue
        self.stop()
        print("Got to home position")

    def move_to_home_old(self):
        t = time.time()
        self._drive_ccw()
        while True:
            if time.time() - t > 2:
                print(
                    "Moved for 2 seconds towards reset, not home yet, reverse direction"
                )
                break
            if self.at_reset():
                print("Got to reset position, reverse direction to get home")
                break
            if self.at_home():
                print("Got to home position")
                self.stop()
                print(self.get_angle())
                return
        self.stop()

        self._drive_cw()
        while True:
            if self.at_home():
                print("Got to home position")
                self.stop()
                print(self.get_angle())
                return
            if self.at_trigger():
                print("Got to trigger position, now how did I get here?????")
                self.stop()
                return


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
        self.pwm_instance.duty_u16(int(duty * 65535 / 100))

    def beep_trap_ready(self):
        for i in range(5):
            sleep(0.5)
            self.on()
            sleep(0.5)
            self.off()
        print("Trap is ready.")

    def beep_error(self, beeps, loop=True):
        while True:
            self.on()
            sleep(5)
            self.off()
            sleep(1)
            for i in range(beeps):
                self.on()
                sleep(0.1)
                self.off()
                sleep(0.1)
            sleep(1)
            if not loop:
                break


class RotaryEncoder:
    def __init__(self):
        self.pin_1 = Pin(PIN_ROT_ENC_1, Pin.IN, Pin.PULL_UP)
        self.pin_2 = Pin(PIN_ROT_ENC_2, Pin.IN, Pin.PULL_UP)
        self.pin_4 = Pin(PIN_ROT_ENC_4, Pin.IN, Pin.PULL_UP)
        self.pin_8 = Pin(PIN_ROT_ENC_8, Pin.IN, Pin.PULL_UP)

    def position(self):
        return 15 - self.pin_1.value() - 2*self.pin_2.value() - 4*self.pin_4.value() - 8*self.pin_8.value()

class TriggerWindow:
    def __init__(self):
        self.pin = Pin(PIN_SW_TRIGGER_WINDOW, Pin.IN, Pin.PULL_UP)
        self.i2c = i2c

    def _is_night(self):
        return True ## TODO

class Clock:
    def __init__(self):
        self.i2c = I2C(id=0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))
        self.r = pcf8563.PCF8563(self.i2c)
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
        if self.night_only.value():
            return self.is_night()
        return True

    def check_low_voltage(self):
        return self.r.check_low_voltage()


class RP_UART:
    def __init__(self):
        self.uart = UART(0, baudrate=9600, tx=Pin(PIN_UART_TX), rx=Pin(PIN_UART_RX))

    def read_line_from_uart(self):
        line = bytearray()
        while True:
            if self.uart.any():
                char = self.uart.read(1)
                if char == b"\n":
                    break
                line.extend(char)
        return line

    def wait_for_line(self, line):
        while True:
            if bytearray(line) == self.read_line_from_uart():
                break


class Servo:
    def __init__(self, signal_pin, en_pin):
        self.signal = PWM(Pin(signal_pin))
        self.signal.freq(50)
        self.en = Pin(en_pin, Pin.OUT)

        self.disable_signal()
        self.off()

    def duty_ns(self, duty_ns):
        self.signal.duty_ns(duty_ns)

    def on(self):
        self.en.value(True)

    def off(self):
        self.en.value(False)

    # This disables sending any signal to the servo so when it is powered on it won't move.
    def disable_signal(self):
        self.signal.duty_ns(0)

    # Helper function to move servos at a set speed
    # angle_duty_start - the angle to start at in nanoseconds
    # angle_duty_end - the angle to move to in nanoseconds
    # speed - the speed in nanoseconds per second
    def move(self, angle_duty_start, angle_duty_end, speed):
        steps_per_second = 50
        total_steps = int(
            abs(angle_duty_end - angle_duty_start) / speed * steps_per_second
        )
        step_size = (angle_duty_end - angle_duty_start) / total_steps

        for i in range(total_steps):
            angle_duty = angle_duty_start + step_size * i
            self.duty_ns(int(angle_duty))
            sleep(1 / steps_per_second)

        self.duty_ns(angle_duty_end)


class PIRs:
    def __init__(self):
        self.pir_1 = Pin(PIN_PIR_1, Pin.IN)
        self.pir_2 = Pin(PIN_PIR_2, Pin.IN)
        self.set_pir_sensitivity(128)
        # self.pir_sensitivity = ADC(Pin(PIN_RPI_SENSE_POT, Pin.IN))
        # self.set_pir_sensitivity(PIR_SENSITIVITY)

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
        i2c.writeto(0x3E, bytes([0, value]))


class Trap:
    def __init__(self, i2c):
        self.i2c = i2c

        self.set_pir_sensitivity(PIR_SENSITIVITY)

        self.spool_power = Pin(PIN_6V_EN, Pin.OUT)
        self.spool_power.low()

        self.servo_1 = Servo(PIN_SERVO_1_SIG, PIN_SERVO_1_EN)
        self.servo_2 = Servo(PIN_SERVO_2_SIG, PIN_SERVO_2_EN)

        self.spool_1 = Spool(self.servo_1, SERVO_TRIGGER, SERVO_HOME, SERVO_RESET)
        self.spool_2 = Spool(self.servo_2, SERVO_TRIGGER, SERVO_HOME, SERVO_RESET)

        self.pir_sensitivity = ADC(Pin(PIN_RPI_SENSE_POT, Pin.IN))

        self.pir_1 = Pin(PIN_PIR_1, Pin.IN)
        self.pir_2 = Pin(PIN_PIR_2, Pin.IN)

        self.led = Pin(PIN_LED_1, Pin.OUT)

        self.state = None

    def read_pir_sensitivity(self):
        voltage = (self.pir_sensitivity.read_u16() / 65535) * 3.3
        max_voltage = self.pot_r_to_voltage(9.92)
        value = int((voltage / max_voltage) * 127)
        value = 127 - value
        return value

    def pot_r_to_voltage(self, r):
        return r / (27 + r) * 3.3

    def set_pir_sensitivity(self, value):
        value = 127 - value
        bytearray(0) + bytearray([value])
        if value >= 128:
            value = 128
        if value < 0:
            value = 0
        self.i2c.writeto(0x3E, bytes([0, value]))

    def trigger_spools(self):
        self.state = "triggering"
        print("Triggering spools")
        # Set initial state to off and no signal.
        self.spool_1.off()
        self.spool_2.off()

        # Power up servos
        self.spool_power.high()
        sleep(0.1)
        self.spool_1.on()
        self.spool_2.on()
        sleep(0.4)

        # Trigger spools
        self.spool_1.trigger()
        self.spool_2.trigger()
        sleep(1)

        # Move them back home
        self.spool_1.home()
        sleep(1)
        self.spool_2.home()
        sleep(1)

        # Turn off power
        self.spool_power.low()
        self.spool_1.off()
        self.spool_2.off()

        # Update state
        self.state = "triggered"

    def reset_spool(self, spool):
        self.state = "resetting"
        self.spool_power.high()
        spool.disable_signal()
        spool.on()
        sleep(0.1)

        print("Reset")
        n = 5  # Number of reset steps taken
        speed = abs(SERVO_RESET - SERVO_HOME) / 6
        for i in range(n):
            angle = int(SERVO_HOME + (SERVO_RESET - SERVO_HOME) * (i + 1) / n)
            print(angle)
            self.move_spool(spool, SERVO_HOME, angle, speed)
            spool.duty_ns(angle)
            sleep(2)
            self.move_spool(spool, angle, SERVO_HOME, speed)
            sleep(2)
        spool.duty_ns(SERVO_RESET)
        sleep(2.5)
        print("Home")
        spool.duty_ns(SERVO_HOME)
        sleep(2)
        self.spool.off()
        self.spool_power.low()
        self.state = "reset"

    def reset_spools(self):
        self.spool_power.high()
        print("Reset spool 1")
        self.spool_1.reset()
        # self.reset_spool(self.spool1)
        print("Reset spool 2")
        self.spool_2.reset()
        # self.reset_spool(self.spool2)
        print("Finished resetting spools, waiting 1 second.")
        sleep(1)

    def check_pirs(self):
        # print(self.pir1.value())
        # print(self.pir2.value())
        return self.pir1.value() or self.pir2.value()

    def write_led(self, on):
        self.led.value(on)

    # Helper function to move servos
    # spool - the spool to move
    # angle_duty_start - the angle to start at in nanoseconds
    # angle_duty_end - the angle to move to in nanoseconds
    # speed - the speed in nanoseconds per second
    def move_spool(self, spool, angle_duty_start, angle_duty_end, speed):

        steps_per_second = 50
        total_steps = int(
            abs(angle_duty_end - angle_duty_start) / speed * steps_per_second
        )
        step_size = (angle_duty_end - angle_duty_start) / total_steps

        for i in range(total_steps):
            angle_duty = angle_duty_start + step_size * i
            spool.duty_ns(int(angle_duty))
            sleep(1 / steps_per_second)

        spool.duty_ns(angle_duty_end)



