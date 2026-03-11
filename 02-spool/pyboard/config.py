# H bridge driver pins
PIN_H_IN_1 = 9
PIN_H_IN_2 = 10

# Rotary encoder pins
PIN_ROT_ENC_1 = 4
PIN_ROT_ENC_2 = 5
PIN_ROT_ENC_4 = 3
PIN_ROT_ENC_8 = 6

# I2C pins
PIN_SDA = 16
PIN_SCL = 17

# PIR pins
PIN_PIR_1 = 13
PIN_PIR_2 = 12
PIR_SENSITIVITY = 127 # 0-127

# Buzzer Pin
PIN_BUZZER = 1

# Night time switch
PIN_SW_NIGHT_ONLY = 0 # Setup with pull-up

# Photo interrupter pins
PIN_EN_PHOTO_INTERRUPTER = 11
PIN_PHOTO_INTERRUPTER_HOME = 15
PIN_PHOTO_INTERRUPTER_RESET = 14

# Electromagnet
PIN_ELECTROMAGNET_RELEASE = 18

# UART pins
PIN_UART_TX = 28
PIN_UART_RX = 29

# Position (Used for day and night calculations)
LATITUDE = -43.532055
LONGITUDE = 172.636230

# Error codes
ERROR_TIME_NOT_SET = 3
ERROR_NO_PROGRAM_FOUND = 4
ERROR_MOVEMENT_TIMEOUT = 5
CANNOT_FIND_HOME = 6
ERROR_OVER_CURRENT = 7

# Guess as to how long it takes to get from home to reset
# This is used so when resetting the first time it knows how long each "step" should be.
HOME_TO_RESET_DURATION = 10

# INA219 shunt resistor resistance in Ω
SHUNT_OHMS = 0.1

# Mas current in mA
MAX_CURRENT = 1200
