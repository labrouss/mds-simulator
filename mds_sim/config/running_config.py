"""In-memory running configuration object graph for one switch instance."""

from dataclasses import dataclass, field
from ..hardware.chassis import Chassis
from ..fabric.vsan import VSANDatabase
from ..fabric.zoning import ZoningEngine
from ..fabric.flogi_db import FlogiDatabase
from ..fabric.domain_manager import DomainManager
from ..logging_.event_log import EventLog


@dataclass
class RunningConfig:
    hostname: str
    chassis: Chassis = None
    vsan_db: VSANDatabase = field(default_factory=VSANDatabase)
    zoning: ZoningEngine = field(default_factory=ZoningEngine)
    flogi_db: FlogiDatabase = field(default_factory=FlogiDatabase)
    domain_mgr: DomainManager = field(default_factory=DomainManager)
    event_log: EventLog = field(default_factory=EventLog)

    def __post_init__(self):
        if self.chassis is None:
            self.chassis = Chassis(hostname=self.hostname)

    def to_dict(self):
        return {
            "hostname": self.hostname,
            "mgmt_ip": self.chassis.mgmt_ip,
            "mgmt_mask": self.chassis.mgmt_mask,
            "mgmt_gateway": self.chassis.mgmt_gateway,
            "vsans": self.vsan_db.show(),
            "ports": {
                name: {
                    "admin_state": p.admin_state,
                    "port_mode": p.port_mode,
                    "speed_config": p.speed_config,
                    "vsan": p.vsan,
                    "trunk_allowed_vsans": p.trunk_allowed_vsans,
                    "sfp_type": p.sfp_type,
                }
                for name, p in self.chassis.ports.items()
            },
        }

    def load_dict(self, data: dict):
        self.hostname = data.get("hostname", self.hostname)
        self.chassis.mgmt_ip = data.get("mgmt_ip")
        self.chassis.mgmt_mask = data.get("mgmt_mask")
        self.chassis.mgmt_gateway = data.get("mgmt_gateway")
        for vsan in data.get("vsans", []):
            self.vsan_db.create(vsan["vsan"], vsan.get("name", ""))
        for name, pdata in data.get("ports", {}).items():
            if name in self.chassis.ports:
                p = self.chassis.ports[name]
                p.admin_state = pdata.get("admin_state", "down")
                p.port_mode = pdata.get("port_mode", "auto")
                p.speed_config = pdata.get("speed_config", "auto")
                p.vsan = pdata.get("vsan", 1)
                p.trunk_allowed_vsans = pdata.get("trunk_allowed_vsans", [1])
                if pdata.get("sfp_type"):
                    p.insert_sfp(pdata["sfp_type"])
