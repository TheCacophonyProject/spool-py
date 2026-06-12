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

# Switch pins
PIN_SW_1 = 8
PIN_SW_2 = 7

# Spool reed switch pin
PIN_SPOOL_RESET = 22

# INA219 shunt resistor resistance in Ω
SHUNT_OHMS = 0.1

# Error codes
ERROR_TIME_NOT_SET = 3
ERROR_NO_PROGRAM_FOUND = 4
ERROR_MOVEMENT_TIMEOUT = 5
ERROR_FAILED_TO_RESET = 6
ERROR_OVER_CURRENT = 7
ERROR_RUNTIME_ERROR = 8
ERROR_SPOOL_NOT_RELEASING = 9

# Indicator LEDs
PIN_LED_1 = 7   # PIR trigger
PIN_LED_2 = 8   # thermal trigger

# This is used so when resetting the first time it knows how long each "step" should be.
HOME_TO_RESET_DURATION = 13

class UserConfig():
    def __init__(self):
        self.apir_d_threshold = 0.3
        self.apir_dt_threshold = 450
        self.max_current = 1000
        self.spool_reset_delay_minutes = 10
        self.latitude = -43.532055
        self.longitude = 172.636230
        self.test_loop_interval = 180
        self.switch_1_disable = "IGNORE"
        self.switch_2_disable = "IGNORE"
        self.switch_logic = "OR"
        self.observation_mode = False
        self.motion_message_gap = 10
        self.post_reset_cooldown_seconds = 20
        self.spool_reed_check = False

        self._load_user_config()

    def _load_user_config(self):
        try:
            import json
            with open("config.json") as f:
                user_cfg = json.load(f)
            for key, value in user_cfg.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except (OSError, ValueError):
            pass
