"""Startup-config persistence (JSON on disk, one file per switch)."""

import json
import pathlib


class ConfigStore:
    def __init__(self, switch_name, base_dir="configs"):
        self.path = pathlib.Path(base_dir) / f"{switch_name}_startup.json"

    def save(self, running_config_dict: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(running_config_dict, indent=2))

    def load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {}

    def erase(self):
        if self.path.exists():
            self.path.unlink()

    def exists(self) -> bool:
        return self.path.exists()
