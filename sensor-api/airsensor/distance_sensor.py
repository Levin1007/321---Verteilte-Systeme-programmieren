#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author : www.modmypi.com
# Link: https://www.modmypi.com/blog/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi

import RPi.GPIO as GPIO
import time


class DistanceSensor:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)  # Setze die GPIO Boardkonfiguration ein.

        self.TRIG = 36  # Variablendeklaration
        self.ECHO = 32  # Variablendeklaration

        GPIO.setup(self.TRIG, GPIO.OUT)  # Variable TRIG als Output festlegen.
        GPIO.setup(self.ECHO, GPIO.IN)  # Variable ECHO als Input festlegen.

        GPIO.output(self.TRIG, False)

    def read(self):
        GPIO.output(self.TRIG, True)  # Sendet ein Ultraschallsignal
        time.sleep(0.00001)  # Wartet 0,00001 Sekunden
        GPIO.output(self.TRIG, False)  # Beendet das senden des Ultraschallsignals

        while GPIO.input(self.ECHO) == 0:
            pulse_start = time.time()

        while GPIO.input(self.ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start  # Berechnung für die Dauer Des Pulses
        distance = pulse_duration * 17150  # Berechnung zur Bestimmung der Entfernung.
        distance = round(distance, 2)  # Ergebnis wird auf 2 Nachkommastellen gerundet.
        return distance
 