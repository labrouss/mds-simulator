"""Ring-buffer syslog-style event log shared across CLI and NX-API."""

from collections import deque
from datetime import datetime


class EventLog:
    def __init__(self, maxlen=1000):
        self._buf = deque(maxlen=maxlen)

    def emit(self, message: str):
        ts = datetime.utcnow().strftime("%Y %b %d %H:%M:%S")
        entry = f"{ts} switch {message}"
        self._buf.append(entry)
        return entry

    def tail(self, n=20):
        return list(self._buf)[-n:]

    def all(self):
        return list(self._buf)
