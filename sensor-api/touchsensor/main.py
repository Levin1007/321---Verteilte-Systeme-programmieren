from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from threading import Thread

from touchsensor import TouchSensor


touch_sensor = TouchSensor()
Thread(target=touch_sensor.watch, daemon=True).start()


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"touched": touch_sensor.read_touch()}).encode())


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8081), Server)
    print("Touch-sensor server listening on 0.0.0.0:8081")
    server.serve_forever()
