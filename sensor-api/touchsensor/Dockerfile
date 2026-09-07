FROM python:3.12

WORKDIR /usr/src/app
RUN pip install --no-cache-dir RPi.GPIO

COPY touchsensor.py main.py ./
CMD ["python", "-u", "main.py"]
