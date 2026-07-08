"""Zone / zoneset management."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Zone:
    name: str
    members: List[str] = field(default_factory=list)


@dataclass
class ZoneSet:
    name: str
    zones: List[str] = field(default_factory=list)


class ZoningEngine:
    def __init__(self):
        self.zones: Dict[int, Dict[str, Zone]] = {}      # vsan -> name -> Zone
        self.zonesets: Dict[int, Dict[str, ZoneSet]] = {}
        self.active_zoneset: Dict[int, str] = {}

    def create_zone(self, vsan: int, name: str):
        self.zones.setdefault(vsan, {})
        self.zones[vsan].setdefault(name, Zone(name=name))
        return self.zones[vsan][name]

    def add_member(self, vsan: int, zone_name: str, member: str):
        zone = self.create_zone(vsan, zone_name)
        if member not in zone.members:
            zone.members.append(member)

    def create_zoneset(self, vsan: int, name: str):
        self.zonesets.setdefault(vsan, {})
        self.zonesets[vsan].setdefault(name, ZoneSet(name=name))
        return self.zonesets[vsan][name]

    def add_zone_to_zoneset(self, vsan: int, zoneset_name: str, zone_name: str):
        zs = self.create_zoneset(vsan, zoneset_name)
        if zone_name not in zs.zones:
            zs.zones.append(zone_name)

    def activate(self, vsan: int, zoneset_name: str):
        if vsan in self.zonesets and zoneset_name in self.zonesets[vsan]:
            self.active_zoneset[vsan] = zoneset_name
            return True
        return False

    def show_active(self, vsan: int):
        name = self.active_zoneset.get(vsan)
        if not name:
            return None
        zs = self.zonesets[vsan][name]
        return {
            "zoneset": zs.name,
            "zones": [
                {"name": z, "members": self.zones[vsan][z].members}
                for z in zs.zones if z in self.zones.get(vsan, {})
            ],
        }
