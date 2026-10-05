# Prüfung 2 - Sensor API

## Aufgabe

Dieser Service liest die Temperatur und Luftfeuchtigkeit mit dem DHT11 aus. Zusätzlich wird die Helligkeit mit dem BH1750 Lichtsensor gemessen. Die Werte sind als JSON über eine HTTP-API erreichbar.

Bei jedem HTTP-Request wird eine MQTT-Nachricht an den zentralen Broker gesendet.

## Voraussetzungen

- Raspberry Pi mit Joy-Pi-Koffer
- Docker und Docker Compose installiert
- I2C aktiviert: `sudo raspi-config` -> **Interface Options** -> **I2C**
- Die Schaltergruppen auf dem Joy-Pi für DHT11 und Lichtsensor stehen auf `OFF`
- Verbindung zum Netzwerk mit dem MQTT-Broker `10.5.61.199`

Der DHT11 verwendet den physischen GPIO-Pin 7. Der BH1750 verwendet I2C-Bus 1 mit der Adresse `0x5c`.

## Starten

Alle Befehle werden im Ordner `Prüfung_2` ausgeführt:

```bash
cd Prüfung_2
cp .env.example .env
docker compose up --build -d
```

Logs anzeigen:

```bash
docker compose logs -f sensor-api
```

Service stoppen:

```bash
docker compose down
```

## JSON-API testen

Die API läuft auf Port 5000. Auf dem Raspberry Pi:

```bash
curl http://localhost:5000/api/sensors
```

Von einem anderen Computer im gleichen Netzwerk:

```bash
curl http://<IP-DES-RASPI>:5000/api/sensors
```

Beispielantwort:

```json
{
  "sensors": {
    "temperature": {"value": 26.1, "unit": "°C"},
    "humidity": {"value": 28.0, "unit": "%"},
    "light": {"value": 290.0, "unit": "lx"}
  }
}
```

Der DHT11 wird im Hintergrund alle zwei Sekunden ausgelesen. Falls er noch keinen gültigen Wert liefert, stehen Temperatur und Luftfeuchtigkeit zuerst auf `null`. Im Feld `errors` steht dann die Fehlermeldung. Der Lichtsensor kann trotzdem bereits Werte liefern.

## MQTT

Broker und Port:

```text
10.5.61.199:1883
```

Bei jedem Aufruf der API wird eine nicht gespeicherte MQTT-Nachricht gesendet:

```text
Topic: raspi/10/http/request
retain: false
```

Der Inhalt enthält Zeitstempel, HTTP-Methode und Pfad.

Zusätzlich gibt es eine Statusmeldung:

```text
Topic: raspi/10/up
Beim Start: true
Beim Stoppen oder unerwartetem Abbruch: false
```

Die Statusmeldung ist retained. Dadurch sieht man beim Abonnieren direkt, ob der Service läuft.

MQTT testen:

```bash
sudo apt update
sudo apt install -y mosquitto-clients
```

In Terminal 1:

```bash
mosquitto_sub -h 10.5.61.199 -p 1883 -t "raspi/10/#" -v
```

In Terminal 2:

```bash
curl http://localhost:5000/api/sensors
```

Dann sollte in Terminal 1 eine Nachricht auf `raspi/10/http/request` erscheinen. Nach `docker compose down` erscheint auf `raspi/10/up` der Wert `false`.

## Konfiguration

Die Werte können in der Datei `.env` angepasst werden:

```env
HTTP_PORT=5000
MQTT_HOST=10.5.61.199
MQTT_PORT=1883
MQTT_TOPIC=raspi/10/http/request
MQTT_STATUS_TOPIC=raspi/10/up
I2C_BUS=1
SENSOR_BACKEND=hardware
```

Für einen Test ohne angeschlossene Sensoren kann gesetzt werden:

```env
SENSOR_BACKEND=mock
```

Danach den Container neu erstellen:

```bash
docker compose up --build -d
```

## Abgabe

Für die Abgabe werden diese Dateien benötigt:

```text
app.py
sensors.py
Dockerfile
docker-compose.yml
requirements.txt
.env.example
README.md
```
