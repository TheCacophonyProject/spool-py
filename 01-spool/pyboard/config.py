# H bridge driver pins
PIN_H_IN_1 = 9
PIN_H_IN_2 = 10

# Rotary encoder pins
PIN_ROT_ENC_1 = 5
PIN_ROT_ENC_2 = 4
PIN_ROT_ENC_4 = 3
PIN_ROT_ENC_8 = 6

# Position (Used for day and night calculations)
LATITUDE = -43.532055
LONGITUDE = 172.636230

# Error codes
ERROR_TIME_NOT_SET = 3
ERROR_NO_PROGRAM_FOUND = 4

# I2C pins
PIN_SDA = 16
PIN_SCL = 17

# PIR pins
PIN_PIR_1 = 13
PIN_PIR_2 = 12

# Buzzer Pin
PIN_BUZZER = 1

# Night time switch
PIN_SW_NIGHT_ONLY = 0 # Setup with pull-up

# Photo interrupter pins
PIN_EN_PHOTO_INTERRUPTER = 11
PIN_PHOTO_INTERRUPTER_HOME = 15
PIN_PHOTO_INTERRUPTER_TRIGGER = 14
PIN_PHOTO_INTERRUPTER_RESET = 18


HOME_ANGLE_OFFSET = 20
RESET_ANGLE_OFFSET = 221

"""
Got to reset position
196.6992
Moving to home position.
Got to reset position, reverse direction to get home
Got to home position
31.37695
Moving to trigger position.
Got to trigger position
51.41602
Moving to home position.
Got to home position
38.75977
"""


# Servo positions. Values in microseconds for servo motors.
#SERVO_HOME = 2250*1000
#SERVO_RESET = 545*1000
#SERVO_TRIGGER = 2400*1000


#PIR_SENSITIVITY = 127 # Value from 0 to 127, where 0 is most sensitive and 127 is least sensitive.



#=========== PINS ===========

# UART in and out pins
#PIN_TX_IN = 0
#PIN_RX_IN = 1
#PIN_TX_OUT = 4
#PIN_RX_OUT = 5

# Servo pins
#PIN_SERVO_1_EN = 2
#PIN_SERVO_1_SIG = 3
#PIN_SERVO_2_EN = 7
#PIN_SERVO_2_SIG = 8


# Other
#PIN_LED_1 = 6
#PIN_SW_1 = 9
#PIN_SW_2 = 10

#PIN_6V_EN = 11





#

#PIN_RTC_INT = 23



#PIN_RPI_SENSE_POT = 26

#PIN_RTC_BAT_SENSE = 29
