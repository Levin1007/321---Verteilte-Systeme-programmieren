from time import monotonic, sleep

from RPi import GPIO


TOUCH = 11


class TouchSensor:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(TOUCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.result = self._read_raw()

    @staticmethod
    def _read_raw():
        return GPIO.input(TOUCH) == GPIO.LOW

    def read_touch(self):
        """Return the last stable (debounced) touch state."""
        return self.result

    def watch(self, interval=0.02, debounce=0.02):
        """Poll the GPIO and report a change only after it is stable."""
        stable = self._read_raw()
        candidate = stable
        candidate_since = monotonic()
        self.result = stable

        while True:
            current = self._read_raw()
            now = monotonic()
            if current != candidate:
                candidate = current
                candidate_since = now
            elif candidate != stable and now - candidate_since >= debounce:
                stable = candidate
                self.result = stable
                if stable:
                    print("Touch detected", flush=True)
            sleep(interval)
