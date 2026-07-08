"""Chassis / hardware inventory model."""

from dataclasses import dataclass, field
from typing import Dict
from .port import FCPort
from .environment import EnvironmentState


@dataclass
class Chassis:
    hostname: str
    model: str = "DS-C9148T-24PSK9"
    serial: str = "FOX1234ABCD"
    num_ports: int = 48
    ports: Dict[str, FCPort] = field(default_factory=dict)
    environment: EnvironmentState = field(default_factory=EnvironmentState)
    mgmt_ip: str = None
    mgmt_mask: str = None
    mgmt_gateway: str = None

    def __post_init__(self):
        if not self.ports:
            for i in range(1, self.num_ports + 1):
                name = f"fc1/{i}"
                self.ports[name] = FCPort(name=name)

    def show_hardware(self):
        return {
            "model": self.model,
            "serial": self.serial,
            "num_ports": self.num_ports,
            "hostname": self.hostname,
        }
