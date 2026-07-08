"""CLI mode/context tracking, mirroring NX-OS prompt hierarchy."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CLIContext:
    hostname: str
    mode: str = "exec"              # exec | config | config-if | config-vsan-db | config-zone
    current_interface: Optional[str] = None
    current_vsan: Optional[int] = None
    current_zone: Optional[str] = None
    current_zoneset: Optional[str] = None

    def prompt(self) -> str:
        base = self.hostname
        if self.mode == "exec":
            return f"{base}# "
        if self.mode == "config":
            return f"{base}(config)# "
        if self.mode == "config-if":
            return f"{base}(config-if)# "
        if self.mode == "config-vsan-db":
            return f"{base}(config-vsan-db)# "
        if self.mode == "config-zone":
            return f"{base}(config-zone)# "
        if self.mode == "config-zoneset":
            return f"{base}(config-zoneset)# "
        return f"{base}# "
