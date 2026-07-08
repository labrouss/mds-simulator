"""FLOGI / FCNS name server simulation."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FlogiEntry:
    interface: str
    vsan: int
    fcid: str
    wwn: str
    node_wwn: str = ""


class FlogiDatabase:
    def __init__(self):
        self._entries: List[FlogiEntry] = []

    def add(self, interface: str, vsan: int, fcid: str, wwn: str, node_wwn: str = ""):
        entry = FlogiEntry(interface=interface, vsan=vsan, fcid=fcid, wwn=wwn, node_wwn=node_wwn)
        self._entries.append(entry)
        return entry

    def remove_by_interface(self, interface: str):
        self._entries = [e for e in self._entries if e.interface != interface]

    def show(self, vsan: int = None):
        entries = self._entries
        if vsan is not None:
            entries = [e for e in entries if e.vsan == vsan]
        return [e.__dict__ for e in entries]
