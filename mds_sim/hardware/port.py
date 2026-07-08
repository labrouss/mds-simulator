"""Physical/logical representation of a single FC port."""

from dataclasses import dataclass, field
from typing import Optional, List
from .sfp_profiles import get_profile, DEFAULT_DOM


@dataclass
class FCPort:
    name: str                       # e.g. fc1/1
    admin_state: str = "down"       # down | up
    oper_state: str = "OFFLINE"     # FC port state machine state
    port_mode: str = "auto"         # F | E | TE | auto
    speed_config: str = "auto"
    negotiated_speed: Optional[int] = None
    sfp_present: bool = False
    sfp_type: Optional[str] = None
    dom: dict = field(default_factory=dict)
    vsan: int = 1
    trunk_allowed_vsans: List[int] = field(default_factory=lambda: [1])
    negotiated_trunk_vsans: List[int] = field(default_factory=list)
    trunk_isolated_reason: Optional[str] = None
    vsan_trunk_status: dict = field(default_factory=dict)  # vsan_id -> 'up'|'isolated'
    peer_wwn: Optional[str] = None
    domain_id: Optional[int] = None
    error_disabled_reason: Optional[str] = None
    counters: dict = field(default_factory=lambda: {
        "in_frames": 0, "out_frames": 0, "crc_errors": 0, "link_failures": 0
    })

    def insert_sfp(self, sfp_type: str):
        self.sfp_present = True
        self.sfp_type = sfp_type
        self.dom = dict(DEFAULT_DOM)

    def remove_sfp(self):
        self.sfp_present = False
        self.sfp_type = None
        self.dom = {}
        self.negotiated_speed = None

    def set_speed(self, requested):
        if not self.sfp_present:
            return "%PORT-3-IF_NO_SFP: No transceiver installed on {}".format(self.name)
        profile = get_profile(self.sfp_type)
        if not profile or requested not in profile["supported"]:
            return "%PORT-3-IF_INVALID_SPEED: Speed {} not supported by SFP on {}".format(
                requested, self.name)
        self.speed_config = requested
        if requested == "auto":
            self.negotiated_speed = profile["max_speed"]
        else:
            self.negotiated_speed = requested
        return None

    def brief_row(self):
        return {
            "interface": self.name,
            "vsan": self.vsan,
            "admin": self.admin_state,
            "status": self.oper_state,
            "mode": self.port_mode,
            "speed": self.negotiated_speed or "--",
        }
