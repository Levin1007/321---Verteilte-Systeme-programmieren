"""Sensorzugriff für den Joy-Pi (DHT11 an BOARD-Pin 7 (BCM4) und BH1750 an I2C)."""

import os
import time
import threading


class DHT11Reader:
    """Reads the DHT11 continuously without an arbitrary retry limit."""

    def __init__(self):
        self._lock = threading.Lock()
        self._value = None
        self._error = "DHT11 wird initialisiert"
        threading.Thread(target=self._poll, daemon=True).start()

    def _poll(self):
        while True:
            try:
                import dht11
                import RPi.GPIO as GPIO

                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BOARD)
                sensor = dht11.DHT11(pin=7)

                while True:
                    result = sensor.read()
                    with self._lock:
                        if result.is_valid():
                            self._value = (float(result.temperature), float(result.humidity))
                            self._error = None
                        else:
                            self._error = "DHT11 liefert noch keinen gültigen Messwert; der Reader versucht weiter"
                    time.sleep(2)
            except Exception as exc:
                with self._lock:
                    self._error = str(exc)
                time.sleep(2)

    def read(self):
        with self._lock:
            if self._value is None:
                raise RuntimeError(self._error)
            return self._value


_dht_reader = None
_dht_reader_lock = threading.Lock()

def _read_dht11():
    global _dht_reader
    with _dht_reader_lock:
        if _dht_reader is None:
            _dht_reader = DHT11Reader()
    return _dht_reader.read()


def _read_light():
    from smbus2 import SMBus

    # Joy-Pi-Anleitung: BH1750-Adresse 0x5c, einmalige Messung, 1-Lux-Auflösung.
    with SMBus(int(os.getenv("I2C_BUS", "1"))) as bus:
        bus.write_byte(0x5C, 0x20)
        time.sleep(0.18)
        data = bus.read_i2c_block_data(0x5C, 0x00, 2)
    return round(((data[0] << 8) | data[1]) / 1.2, 2)


def read_sensors():
    """Return JSON-ready sensor values and any individual read errors."""
    values = {
        "temperature": {"value": None, "unit": "°C"},
        "humidity": {"value": None, "unit": "%"},
        "light": {"value": None, "unit": "lx"},
    }
    errors = {}

    if os.getenv("SENSOR_BACKEND", "hardware").lower() == "mock":
        values["temperature"]["value"] = 22.5
        values["humidity"]["value"] = 45.0
        values["light"]["value"] = 120.0
        return values, errors

    try:
        temperature, humidity = _read_dht11()
        values["temperature"]["value"] = temperature
        values["humidity"]["value"] = humidity
    except Exception as exc:
        errors["air"] = str(exc)

    try:
        values["light"]["value"] = _read_light()
    except Exception as exc:
        errors["light"] = str(exc)

    return values, errors
