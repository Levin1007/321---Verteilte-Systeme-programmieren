FROM python:3.12

WORKDIR /usr/src/app
RUN pip install --no-cache-dir RPi.GPIO dht11 smbus2

COPY airsensor.py light_sensor.py main.py ./
COPY static ./static
CMD ["python", "-u", "main.py"]
