"""Fixed-width text formatting mimicking real NX-OS show command output."""


def show_interface_brief(rows):
    header = f'{"Interface":<12}{"Vsan":<6}{"Admin":<8}{"Status":<14}{"Mode":<6}{"Speed":<8}'
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f'{r["interface"]:<12}{r["vsan"]:<6}{r["admin"]:<8}{r["status"]:<14}'
            f'{r["mode"]:<6}{str(r["speed"]):<8}'
        )
    return "\n".join(lines)


def show_flogi_database(entries):
    header = f'{"INTERFACE":<12}{"VSAN":<6}{"FCID":<10}{"PORT NAME":<20}{"NODE NAME":<20}'
    lines = [header, "-" * len(header)]
    for e in entries:
        lines.append(
            f'{e["interface"]:<12}{e["vsan"]:<6}{e["fcid"]:<10}{e["wwn"]:<20}{e.get("node_wwn",""):<20}'
        )
    return "\n".join(lines)


def show_vsan(vsans):
    lines = []
    for v in vsans:
        lines.append(f'vsan {v["vsan"]} information')
        lines.append(f'  name:{v["name"]}  state:{v["state"]}')
        lines.append(f'  interfaces: {", ".join(v["interfaces"]) if v["interfaces"] else "(none)"}')
    return "\n".join(lines)


def show_zoneset_active(zs):
    if not zs:
        return "No active zoneset"
    lines = [f'zoneset name {zs["zoneset"]}']
    for z in zs["zones"]:
        lines.append(f'  zone name {z["name"]}')
        for m in z["members"]:
            lines.append(f'    member pwwn {m}')
    return "\n".join(lines)


def show_transceiver_detail(port):
    if not port.sfp_present:
        return f"{port.name}: SFP not present"
    d = port.dom
    return (
        f"{port.name} sfp is present\n"
        f"  type: {port.sfp_type}\n"
        f"  Temperature: {d.get('temperature_c')} C\n"
        f"  Voltage: {d.get('voltage_v')} V\n"
        f"  Tx Power: {d.get('tx_power_dbm')} dBm\n"
        f"  Rx Power: {d.get('rx_power_dbm')} dBm\n"
        f"  Tx Bias: {d.get('tx_bias_ma')} mA"
    )


def show_interface_trunk(ports):
    lines = []
    for p in ports:
        lines.append(f"{p.name}:")
        lines.append(f"  Port mode: {p.port_mode}")
        lines.append(f"  Status: {p.oper_state}")
        lines.append(f"  Trunk allowed vsans (config): {p.trunk_allowed_vsans}")
        lines.append(f"  Trunk vsans negotiated (up): {p.negotiated_trunk_vsans}")
        if p.vsan_trunk_status:
            lines.append("  Per-VSAN trunk state:")
            for vsan_id, status in sorted(p.vsan_trunk_status.items()):
                lines.append(f"    vsan {vsan_id}: {status}")
        if p.trunk_isolated_reason:
            lines.append(f"  Isolation reason: {p.trunk_isolated_reason}")
    return "\n".join(lines)
