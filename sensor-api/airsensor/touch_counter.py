import json
import os
import threading


class TouchCounter:
    """Persistiert die Anzahl erkannter Berührungen in einer JSON-Datei."""

    def __init__(self, path: str = "/usr/src/app/data/touch_count.json"):
        self.path = path
        self._lock = threading.Lock()
        self._count = self._load()

    def _load(self) -> int:
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return int(json.load(file).get("count", 0))
        except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return 0

    def _save(self) -> None:
        directory = os.path.dirname(self.path)
        os.makedirs(directory, exist_ok=True)
        temporary_path = f"{self.path}.tmp"
        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump({"count": self._count}, file)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, self.path)

    def increment(self) -> int:
        with self._lock:
            self._count += 1
            self._save()
            return self._count

    @property
    def count(self) -> int:
        with self._lock:
            return self._count
