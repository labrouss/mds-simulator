"""Ring-buffer syslog-style event log shared across CLI and NX-API.

Supports subscriber callbacks so a WebSocket layer can push new events
to connected instructor dashboards in real time.
"""

from collections import deque
from datetime import datetime


class EventLog:
    def __init__(self, maxlen=1000):
        self._buf = deque(maxlen=maxlen)
        self._subscribers = []

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def emit(self, message: str):
        ts = datetime.utcnow().strftime("%Y %b %d %H:%M:%S")
        entry = f"{ts} switch {message}"
        self._buf.append(entry)
        for cb in list(self._subscribers):
            try:
                cb(entry)
            except Exception:
                pass
        return entry

    def tail(self, n=20):
        return list(self._buf)[-n:]

    def all(self):
        return list(self._buf)
