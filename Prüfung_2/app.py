#!/usr/bin/env python3
"""Joy-Pi sensor API using the same HTTPServer approach as sensor-api."""

import json
import logging
import os
import signal
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

from sensors import read_sensors


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("pruefung2")

BROKER_HOST = os.getenv("MQTT_HOST", "10.5.61.199")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "raspi/10/http/request")
MQTT_STATUS_TOPIC = os.getenv("MQTT_STATUS_TOPIC", "raspi/10/up")
status_client = None
HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "5000"))


def publish_request(method: str, path: str) -> None:
    """Publish one non-retained event for every received HTTP request."""
    payload = json.dumps(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "path": path,
        }
    )
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="raspi-10-http-api")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=5)
        client.loop_start()
        info = client.publish(MQTT_TOPIC, payload, qos=0, retain=False)
        info.wait_for_publish(timeout=3)
        if info.rc != mqtt.MQTT_ERR_SUCCESS or not info.is_published():
            raise RuntimeError(f"MQTT publish failed (rc={info.rc})")
        logger.info("Published HTTP request to MQTT topic %s", MQTT_TOPIC)
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except (OSError, RuntimeError):
            pass


def start_status_client():
    """Publish online state and configure an offline last-will message."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="raspi-10-status")
    client.will_set(MQTT_STATUS_TOPIC, payload="false", qos=1, retain=True)
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=15)
        client.loop_start()
        info = client.publish(MQTT_STATUS_TOPIC, "true", qos=1, retain=True)
        info.wait_for_publish(timeout=3)
        if info.rc != mqtt.MQTT_ERR_SUCCESS or not info.is_published():
            raise RuntimeError(f"MQTT status publish failed (rc={info.rc})")
        logger.info("Published service status true to MQTT topic %s", MQTT_STATUS_TOPIC)
        return client
    except Exception:
        logger.exception("Could not publish service-up status to MQTT broker")
        try:
            client.loop_stop()
            client.disconnect()
        except (OSError, RuntimeError):
            pass
        return None


def stop_status_client(client) -> None:
    """Publish offline state during an orderly container shutdown."""
    if client is None:
        return
    try:
        info = client.publish(MQTT_STATUS_TOPIC, "false", qos=1, retain=True)
        info.wait_for_publish(timeout=3)
        if info.rc != mqtt.MQTT_ERR_SUCCESS or not info.is_published():
            raise RuntimeError(f"MQTT status publish failed (rc={info.rc})")
        logger.info("Published service status false to MQTT topic %s", MQTT_STATUS_TOPIC)
    except Exception:
        logger.exception("Could not publish service-down status to MQTT broker")
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except (OSError, RuntimeError):
            pass


class Server(BaseHTTPRequestHandler):
    """HTTP handler matching the implementation style of sensor-api."""

    def send_json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            publish_request("GET", path)
        except Exception:
            logger.exception("Could not publish HTTP request event to MQTT broker")

        if path == "/api/sensors":
            values, errors = read_sensors()
            response = {"sensors": values}
            if errors:
                response["errors"] = errors
            self.send_json(response)
            return

        if path == "/":
            self.send_json({"endpoint": "/api/sensors"})
            return

        if path == "/health":
            self.send_json({"status": "ok"})
            return

        self.send_json({"error": "Not found"}, 404)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("%s - %s", self.client_address[0], format % args)


def main() -> None:
    global status_client
    status_client = start_status_client()
    web_server = HTTPServer((HTTP_HOST, HTTP_PORT), Server)

    def stop_signal(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, stop_signal)
    signal.signal(signal.SIGTERM, stop_signal)
    logger.info("Server started and listens on %s:%s", HTTP_HOST, HTTP_PORT)
    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        web_server.server_close()
        stop_status_client(status_client)


if __name__ == "__main__":
    main()
