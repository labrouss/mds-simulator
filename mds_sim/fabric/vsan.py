"""VSAN database management."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class VSAN:
    vsan_id: int
    name: str = ""
    state: str = "active"
    interfaces: List[str] = field(default_factory=list)


class VSANDatabase:
    def __init__(self):
        self.vsans: Dict[int, VSAN] = {1: VSAN(vsan_id=1, name="default")}

    def create(self, vsan_id: int, name: str = ""):
        if vsan_id not in self.vsans:
            self.vsans[vsan_id] = VSAN(vsan_id=vsan_id, name=name or f"VSAN{vsan_id:04d}")
        return self.vsans[vsan_id]

    def delete(self, vsan_id: int):
        if vsan_id != 1 and vsan_id in self.vsans:
            del self.vsans[vsan_id]

    def assign_interface(self, vsan_id: int, interface: str):
        vsan = self.create(vsan_id)
        if interface not in vsan.interfaces:
            vsan.interfaces.append(interface)

    def show(self):
        return [
            {"vsan": v.vsan_id, "name": v.name, "state": v.state, "interfaces": v.interfaces}
            for v in self.vsans.values()
        ]
