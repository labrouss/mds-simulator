"""Render running-config as NX-OS style text (for show running-config)."""


def to_nxos_text(cfg_dict: dict) -> str:
    lines = [f"hostname {cfg_dict['hostname']}", "!"]
    if cfg_dict.get("mgmt_ip"):
        lines.append("interface mgmt0")
        lines.append(f"  ip address {cfg_dict['mgmt_ip']} {cfg_dict.get('mgmt_mask', '')}".rstrip())
        lines.append("  no shutdown")
        lines.append("!")
    for vsan in cfg_dict.get("vsans", []):
        lines.append(f"vsan {vsan['vsan']} name {vsan['name']}")
    lines.append("!")
    for name, p in cfg_dict.get("ports", {}).items():
        lines.append(f"interface {name}")
        lines.append(f"  switchport mode {p['port_mode']}")
        lines.append(f"  switchport speed {p['speed_config']}")
        lines.append(f"  vsan {p['vsan']}")
        if p["admin_state"] == "up":
            lines.append("  no shutdown")
        else:
            lines.append("  shutdown")
        lines.append("!")
    return "\n".join(lines)
