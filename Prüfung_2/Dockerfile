FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# RPi.GPIO is compiled during installation. The application also needs the
# SMBus device exposed by the host for the BH1750.

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py sensors.py ./

EXPOSE 5000
CMD ["python", "-u", "app.py"]
