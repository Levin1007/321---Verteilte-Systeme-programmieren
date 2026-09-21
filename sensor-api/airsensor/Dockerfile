FROM python:3.12

WORKDIR /usr/src/app
RUN pip install --no-cache-dir RPi.GPIO dht11 smbus2 paho-mqtt

COPY airsensor.py light_sensor.py main.py touch_sensor.py touch_counter.py ./
COPY static ./static
CMD ["python", "-u", "main.py"]


