"""Simulated environmental sensors: fans, PSUs, temperature."""

from dataclasses import dataclass, field


@dataclass
class EnvironmentState:
    fans_ok: bool = True
    psu1_ok: bool = True
    psu2_ok: bool = True
    intake_temp_c: float = 28.0
    outlet_temp_c: float = 34.0

    def show_temp(self):
        return {
            "intake_temp_c": self.intake_temp_c,
            "outlet_temp_c": self.outlet_temp_c,
            "status": "ok" if self.intake_temp_c < 45 else "warning",
        }

    def show_power(self):
        return {"psu1": "ok" if self.psu1_ok else "failed",
                "psu2": "ok" if self.psu2_ok else "failed"}

    def show_fan(self):
        return {"fans": "ok" if self.fans_ok else "failed"}
