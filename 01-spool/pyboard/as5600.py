import machine
import time

class AS5600:
    # AS5600 I2C address
    I2C_ADDR = 0x36

    # Registers
    REG_ANGLE = 0x0E
    REG_RAW_ANGLE = 0x0C
    REG_STATUS = 0x0B
    REG_CONF = 0x07

    def __init__(self, i2c, address=I2C_ADDR):
        self.i2c = i2c
        self.address = address

    def read_raw_angle(self):
        """Read the raw angle (12-bit) from the AS5600."""
        raw_data = self.i2c.readfrom_mem(self.address, self.REG_RAW_ANGLE, 2)
        angle = (raw_data[0] << 8) | raw_data[1]
        return angle

    def read_angle(self):
        """Read the scaled angle (12-bit) from the AS5600."""
        raw_data = self.i2c.readfrom_mem(self.address, self.REG_ANGLE, 2)
        angle = (raw_data[0] << 8) | raw_data[1]
        return angle

    def get_degrees(self):
        """Get the current angle in degrees (0-360)."""
        angle = self.read_angle()
        degrees = (angle * 360) / 4096  # 12-bit resolution (0-4095)
        return degrees

    def get_status(self):
        """Get the status of the sensor."""
        status = self.i2c.readfrom_mem(self.address, self.REG_STATUS, 1)[0]
        magnet_detected = (status & 0x20) != 0
        return {
            "magnet_detected": magnet_detected,
        }

# Example usage:
if __name__ == "__main__":
    i2c = machine.I2C(1, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)
    sensor = AS5600(i2c)

    while True:
        angle = sensor.get_degrees()
        status = sensor.get_status()
        print(f"Angle: {angle:.2f}°, Magnet Detected: {status['magnet_detected']}")
        time.sleep(0.5)
