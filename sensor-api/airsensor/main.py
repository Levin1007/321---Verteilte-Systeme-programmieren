from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep
from airsensor import AirSensor
from distance_sensor import DistanceSensor
from touch_sensor import TouchSensor
from touch_counter import TouchCounter
import json
import textwrap
import threading
import paho.mqtt.client as mqtt
 
 
air_sensor = AirSensor()
distance_sensor = DistanceSensor()
touch_sensor = TouchSensor(11)
touch_counter = TouchCounter()
 
host = "0.0.0.0"
port = 8080
 
sleep(1)
 
class Server(BaseHTTPRequestHandler):
    def sendJSON(self, object: object, code: int = 200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Vary", "Origin")
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(object).encode())
 
    def do_GET(self):
        if self.path == "/":
            air = air_sensor.read_air()
            self.sendJSON({"status": "ok", "air": air.__dict__})
            return

        if self.path == "/distance":
            distance = distance_sensor.read()
            self.sendJSON({"status": "ok", "distance": distance})
            return
 
        if self.path == "/metrics":
            air = air_sensor.read_air()
            distance = distance_sensor.read() or 1
            response = textwrap.dedent(f"""
                # HELP sensor_distance measured distance in lux\n\
                # TYPE sensor_distance gauge\n\
                sensor_distance {distance}\n\
                # HELP sensor_air_temperature measured temperature in celcius\n\
                # TYPE sensor_air_temperature gauge\n\
                sensor_air_temperature {air.temperature}\n\
                # HELP sensor_air_humidity measured humidity in percent\n\
                # TYPE sensor_air_humidity gauge\n\
                sensor_air_humidity {air.humidity}
            """)
 
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Vary", "Origin")
            self.send_header("Content-type", "text/plain")
            self.end_headers()
 
            self.wfile.write(response.encode())
 
 
def read_distance_sensor(delay):
        while True:
            distance = distance_sensor.read()
            mqtt_client.publish("ldirren/sensor/distance", distance, qos=2)
            sleep(delay)


def read_touch_sensor(delay):
    was_touched = False

    while True:
        touched = touch_sensor.read()

        # Nur beim Erkennen einer neuen Berührung senden
        if touched and not was_touched:
            touch_count = touch_counter.increment()
            mqtt_client.publish(
                "ldirren/sensor/touch",
                payload="true",
                qos=2
            )
            mqtt_client.publish(
                "ldirren/sensor/touch/count",
                payload=str(touch_count),
                qos=2,
                retain=True,
            )

        was_touched = touched
        sleep(delay)
 

def on_connect(client, userdata, flags, reason_code, properites):
    print(f"Connected to MQTT Broker with result {reason_code}")


def on_message(client, userdata, msg: object):
    print(msg.topic + " " + str(msg.payload))


mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("172.17.0.1", 1883, 60)
 
def main():
    web_server = HTTPServer((host, port), Server)
    print(f"Server started and listen to {host}:{port}")
 
    distanceSensorThread = threading.Thread(
        target=read_distance_sensor, args=(0.3,)
    )
    distanceSensorThread.start()

    touchSensorThread = threading.Thread(
        target=read_touch_sensor, args=(0.05,), daemon=True
    )
    touchSensorThread.start()
 
    try:
        mqtt_client.loop_start()
        mqtt_client.publish("ldirren/up", "true", qos=2)
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass
 
 
if __name__ == "__main__":
    main()
 
print("Server stopped")
 
 