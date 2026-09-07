from time import sleep

from smbus2 import SMBus


class LightSensor:
    """BH1750 light sensor on the Joy-Pi I2C bus."""

    ADDRESS = 0x5C
    ONE_TIME_HIGH_RES_MODE = 0x20

    def __init__(self, bus_number=1):
        self.bus = SMBus(bus_number)

    def read_light(self):
        data = self.bus.read_i2c_block_data(self.ADDRESS, self.ONE_TIME_HIGH_RES_MODE, 2)
        sleep(0.18)
        return round((data[1] + (256 * data[0])) / 1.2, 2)
