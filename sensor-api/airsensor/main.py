import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from airsensor import AirSensor
from light_sensor import LightSensor


try:
    air_sensor = AirSensor()
    air_sensor_error = None
except Exception as error:
    air_sensor = None
    air_sensor_error = str(error)

try:
    light_sensor = LightSensor()
    light_sensor_error = None
except Exception as error:
    light_sensor = None
    light_sensor_error = str(error)


STATIC_ROOT = Path(__file__).parent / "static"


class Server(BaseHTTPRequestHandler):
    def send_json(self, payload, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def send_metrics(self):
        illuminance = None
        light_available = light_sensor is not None
        if light_sensor is not None:
            try:
                illuminance = light_sensor.read_light()
            except OSError:
                light_available = False

        lines = [
            "# HELP sensor_air_available Air sensor availability (1 is available).",
            "# TYPE sensor_air_available gauge",
            f"sensor_air_available {1 if air_sensor is not None else 0}",
            "# HELP sensor_light_available Light sensor availability (1 is available).",
            "# TYPE sensor_light_available gauge",
            f"sensor_light_available {1 if light_available else 0}",
        ]
        if air_sensor is not None:
            try:
                air = air_sensor.read_air()
                if air.is_valid():
                    lines.extend([
                        "# HELP sensor_temperature_celsius Current temperature in Celsius.",
                        "# TYPE sensor_temperature_celsius gauge",
                        f"sensor_temperature_celsius {air.temperature}",
                        "# HELP sensor_humidity_percent Current relative humidity in percent.",
                        "# TYPE sensor_humidity_percent gauge",
                        f"sensor_humidity_percent {air.humidity}",
                    ])
            except (OSError, TimeoutError):
                pass
        if illuminance is not None:
            lines.extend([
                "# HELP sensor_light_lux Current illuminance in lux.",
                "# TYPE sensor_light_lux gauge",
                f"sensor_light {illuminance}",
            ])

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(("\n".join(lines) + "\n").encode())

    def serve_static(self):
        file_path = STATIC_ROOT / "index.html"
        mime_type, _ = mimetypes.guess_type(file_path.name)
        self.send_response(200)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def do_GET(self):
        if self.path == "/metrics":
            self.send_metrics()
            return

        if self.path == "/":
            self.serve_static()
        elif self.path == "/api/air":
            if air_sensor is None:
                self.send_json({"status": "error", "message": air_sensor_error}, 503)
                return
            air = air_sensor.read_air()
            self.send_json({"status": "ok", "data": [
                {"label": "Temperature", "value": air.temperature, "unit": "°C"},
                {"label": "Humidity", "value": air.humidity, "unit": "%"},
            ]})
        elif self.path == "/api/light":
            if light_sensor is None:
                self.send_json({"status": "error", "message": light_sensor_error}, 503)
                return
            try:
                self.send_json({"status": "ok", "data": {
                    "label": "Illuminance", "value": light_sensor.read_light(), "unit": "lux",
                }})
            except OSError as error:
                self.send_json({"status": "error", "message": str(error)}, 503)
        else:
            self.send_error(404)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Server)
    print("Sensor API listening on 0.0.0.0:8080")
    server.serve_forever()
