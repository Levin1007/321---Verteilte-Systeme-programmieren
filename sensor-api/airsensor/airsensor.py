from time import sleep
import threading

import RPi.GPIO as GPIO
import dht11


GPIO.setmode(GPIO.BOARD)


class AirSensor:
    def __init__(self):
        self.instance = dht11.DHT11(pin=7)
        self.result = self.instance.read()
        print(self.result.__dict__)
        threading.Thread(target=self.update, daemon=True).start()

    def update(self):
        while True:
            readout = self.instance.read()
            if readout.is_valid():
                print(f"Temperature: {readout.temperature}°C Humidity: {readout.humidity}%")
                self.result = readout
            else:
                sleep(2)

    def read_air(self):
        return self.result
