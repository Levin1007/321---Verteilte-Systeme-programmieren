#!/usr/bin/env python
from typing import Callable
from RPi import GPIO


class TouchSensor:
    def __init__(self, pin: int):
        self.pin = pin
        self.external_callback: Callable[[bool], None] | None = None

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def _internal_callback(self, channel: int):
        is_touched = GPIO.input(channel) == GPIO.LOW

        if self.external_callback:
            self.external_callback(is_touched)

    def start(self, callback: Callable[[bool], None]):
        self.external_callback = callback
        GPIO.add_event_detect(
            self.pin,
            GPIO.BOTH,
            callback=self._internal_callback,
            bouncetime=50,
        )

    def read(self) -> bool:
        return GPIO.input(self.pin) == GPIO.LOW

    def close(self):
        GPIO.remove_event_detect(self.pin)
        GPIO.cleanup(self.pin)