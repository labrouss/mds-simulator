"""E-port / TE-port link negotiation helper (local side of fabric_bus)."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EPortLink:
    local_port: str
    remote_switch: str = None
    remote_port: str = None
    trunk_allowed_vsans: List[int] = field(default_factory=lambda: [1])
    established: bool = False

    def negotiate(self, peer_vsans: List[int]):
        common = sorted(set(self.trunk_allowed_vsans) & set(peer_vsans))
        self.established = len(common) > 0
        return common
