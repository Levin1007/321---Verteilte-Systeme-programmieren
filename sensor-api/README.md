# Separate sensor containers

Each folder is an independent Docker project. Start the air sensor on port 8080:

```sh
cd airsensor
docker compose up --build
```

This is the central sensor API. Its endpoints are `/api/air`, `/api/light`,
and `/metrics`. The added BH1750 light sensor uses I2C bus 1. Enable I2C on
the Raspberry Pi and set all Joy-Pi module switches to `OFF`.

Start the touch sensor on port 8081:

```sh
cd touchsensor
docker compose up --build
```

The touch sensor deliberately uses polling instead of `GPIO.add_event_detect`,
which requires exclusive GPIO event-line access and caused the `Failed to add
edge detection` message in the combined container. Its poller logs `Touch
detected` after a stable touch. For the Joy-Pi touch sensor, set all switches
of both switch banks to `OFF`, as required by the board manual.

Open `http://<PI-IP-ADDRESS>:8080/` in a browser for the API overview page.

Start the monitoring stack from `system-monitoring` with `docker compose up -d`.
Grafana on port 3000 provisions two alert rules: illuminance below 10 lux and
an unavailable light sensor.
