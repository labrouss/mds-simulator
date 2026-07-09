"""Command dispatcher: routes CLI input lines to handler functions
based on current CLIContext mode. Supports partial/abbreviated matching.
"""

import shlex
from .modes import CLIContext
from .output_templates import (
    show_interface_brief, show_flogi_database, show_vsan,
    show_zoneset_active, show_transceiver_detail, show_interface_trunk
)
from ..hardware.port_state_machine import PortStateMachine
from . import command_tree as ct


class Dispatcher:
    def __init__(self, running_config, fault_injector, state_machines, config_store):
        self.cfg = running_config
        self.fi = fault_injector
        self.sm = state_machines
        self.store = config_store
        self.ctx = CLIContext(hostname=self.cfg.hostname)

    def execute(self, line: str) -> str:
        line = line.strip()
        if not line:
            return ""
        try:
            tokens = shlex.split(line)
        except ValueError:
            return "% Invalid input"

        tokens = ct.resolve_tokens(self.ctx.mode, tokens)

        try:
            if self.ctx.mode == "exec":
                return self._exec_mode(tokens)
            elif self.ctx.mode == "config":
                return self._config_mode(tokens)
            elif self.ctx.mode == "config-if":
                return self._config_if_mode(tokens)
            elif self.ctx.mode == "config-vsan-db":
                return self._config_vsan_db_mode(tokens)
            elif self.ctx.mode == "config-zone":
                return self._config_zone_mode(tokens)
            elif self.ctx.mode == "config-zoneset":
                return self._config_zoneset_mode(tokens)
        except Exception as e:
            return f"% Error: {e}"
        return "% Invalid command"

    # ---------- EXEC mode ----------
    def _exec_mode(self, t):
        cmd = t[0]
        if cmd in ("configure",) and (len(t) == 1 or t[1] == "terminal"):
            self.ctx.mode = "config"
            return ""
        if cmd == "show":
            return self._show(t[1:])
        if cmd == "copy" and t[1:3] == ["running-config", "startup-config"]:
            self.store.save(self.cfg.to_dict())
            return "[########################################] 100%\nCopy complete."
        if cmd == "write" and len(t) > 1 and t[1] == "erase":
            self.store.erase()
            return "This command will erase the startup-configuration.\nAre you sure? [confirm]\ny"
        if cmd == "reload":
            self.cfg.load_dict(self.store.load())
            return "Reloading switch from startup-config..."
        return "% Invalid command at exec mode"

    def _show(self, t):
        if not t:
            return "% Incomplete command"
        if t[0] == "interface" and len(t) > 1 and t[1] == "brief":
            rows = [p.brief_row() for p in self.cfg.chassis.ports.values()]
            return show_interface_brief(rows)
        if t[0] == "interface" and len(t) > 2 and t[2] == "transceiver":
            port = self.cfg.chassis.ports.get(t[1])
            return show_transceiver_detail(port) if port else "% Invalid interface"
        if t[0] == "interface" and len(t) > 2 and t[2] == "trunk":
            port = self.cfg.chassis.ports.get(t[1])
            return show_interface_trunk([port]) if port else "% Invalid interface"
        if t[0] == "trunk":
            eports = [p for p in self.cfg.chassis.ports.values() if p.port_mode in ("E", "TE")]
            return show_interface_trunk(eports) if eports else "No trunking interfaces configured"
        if t[0] == "flogi" and t[1] == "database":
            return show_flogi_database(self.cfg.flogi_db.show())
        if t[0] == "vsan":
            return show_vsan(self.cfg.vsan_db.show())
        if t[0] == "zoneset" and len(t) > 1 and t[1] == "active":
            vsan = int(t[3]) if "vsan" in t else 1
            return show_zoneset_active(self.cfg.zoning.show_active(vsan))
        if t[0] == "running-config":
            from ..config.serializer import to_nxos_text
            return to_nxos_text(self.cfg.to_dict())
        if t[0] == "hardware":
            return str(self.cfg.chassis.show_hardware())
        if t[0] == "environment":
            env = self.cfg.chassis.environment
            return f"{env.show_temp()}\n{env.show_power()}\n{env.show_fan()}"
        if t[0] == "logging":
            return "\n".join(self.cfg.event_log.tail(20))
        return "% Invalid show command"

    # ---------- config mode ----------
    def _config_mode(self, t):
        cmd = t[0]
        if cmd == "interface":
            name = t[1]
            if name not in self.cfg.chassis.ports:
                return "% Invalid interface"
            self.ctx.current_interface = name
            self.ctx.mode = "config-if"
            return ""
        if cmd == "vsan" and len(t) > 1 and t[1] == "database":
            self.ctx.mode = "config-vsan-db"
            return ""
        if cmd == "hostname":
            self.cfg.hostname = t[1]
            self.ctx.hostname = t[1]
            return ""
        if cmd == "zone" and t[1] == "name":
            vsan = int(t[t.index("vsan") + 1]) if "vsan" in t else 1
            self.ctx.current_zone = t[2]
            self.ctx.current_vsan = vsan
            self.cfg.zoning.create_zone(vsan, t[2])
            self.ctx.mode = "config-zone"
            return ""
        if cmd == "zoneset" and t[1] == "name":
            vsan = int(t[t.index("vsan") + 1]) if "vsan" in t else 1
            self.ctx.current_zoneset = t[2]
            self.ctx.current_vsan = vsan
            self.cfg.zoning.create_zoneset(vsan, t[2])
            self.ctx.mode = "config-zoneset"
            return ""
        if cmd == "zoneset" and t[1] == "activate":
            vsan = int(t[t.index("vsan") + 1]) if "vsan" in t else 1
            name = t[3]
            ok = self.cfg.zoning.activate(vsan, name)
            return "" if ok else "% Zoneset not found"
        if cmd == "end":
            self.ctx.mode = "exec"
            return ""
        if cmd == "exit":
            self.ctx.mode = "exec"
            return ""
        return "% Invalid command at config mode"

    # ---------- config-if mode ----------
    def _config_if_mode(self, t):
        name = self.ctx.current_interface
        port = self.cfg.chassis.ports[name]
        sm: PortStateMachine = self.sm[name]
        cmd = t[0]

        if cmd == "shutdown":
            sm.admin_down()
            return ""
        if cmd == "no" and t[1] == "shutdown":
            sm.admin_up()
            if port.sfp_present:
                sm.link_signal_detected()
            return ""
        if cmd == "switchport" and t[1] == "speed":
            err = port.set_speed(t[2] if t[2] == "auto" else int(t[2]))
            return err or ""
        if cmd == "switchport" and t[1] == "mode":
            port.port_mode = t[2].upper()
            return ""
        if cmd == "switchport" and t[1] == "trunk" and t[2] == "allowed" and t[3] == "vsan":
            port.trunk_allowed_vsans = [int(v) for v in t[4].split(",")]
            return ""
        if cmd == "vsan":
            vsan_id = int(t[1])
            port.vsan = vsan_id
            self.cfg.vsan_db.assign_interface(vsan_id, name)
            return ""
        if cmd == "ip" and t[1] == "address" and name == "mgmt0":
            self.cfg.chassis.mgmt_ip = t[2]
            self.cfg.chassis.mgmt_mask = t[3] if len(t) > 3 else "255.255.255.0"
            return ""
        if cmd == "exit":
            self.ctx.mode = "config"
            self.ctx.current_interface = None
            return ""
        return "% Invalid command at config-if mode"

    # ---------- config-vsan-db mode ----------
    def _config_vsan_db_mode(self, t):
        if t[0] == "vsan":
            vsan_id = int(t[1])
            name = t[3] if len(t) > 3 and t[2] == "name" else ""
            self.cfg.vsan_db.create(vsan_id, name)
            return ""
        if t[0] == "exit":
            self.ctx.mode = "config"
            return ""
        return "% Invalid command at config-vsan-db mode"

    # ---------- config-zone mode ----------
    def _config_zone_mode(self, t):
        if t[0] == "member":
            member = t[-1]
            self.cfg.zoning.add_member(self.ctx.current_vsan, self.ctx.current_zone, member)
            return ""
        if t[0] == "exit":
            self.ctx.mode = "config"
            return ""
        return "% Invalid command at config-zone mode"

    # ---------- config-zoneset mode ----------
    def _config_zoneset_mode(self, t):
        if t[0] == "member":
            zone_name = t[1]
            self.cfg.zoning.add_zone_to_zoneset(self.ctx.current_vsan, self.ctx.current_zoneset, zone_name)
            return ""
        if t[0] == "exit":
            self.ctx.mode = "config"
            return ""
        return "% Invalid command at config-zoneset mode"
