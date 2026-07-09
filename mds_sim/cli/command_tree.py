"""Command tree providing context-sensitive help (?) and tab-completion.

This is metadata-only: it describes valid keywords per mode/position and
their help text, mirroring NX-OS's "word help" and "command syntax help".
It does not execute commands -- Dispatcher still does that. The tree is
consulted by the SSH server to answer '?' and Tab requests.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CommandNode:
    keyword: str
    help_text: str = ""
    children: Dict[str, "CommandNode"] = field(default_factory=dict)
    # placeholder token, e.g. <interface-name>, <vsan-id> -- always "matches"
    is_placeholder: bool = False

    def add(self, keyword: str, help_text: str = "", is_placeholder=False) -> "CommandNode":
        if keyword not in self.children:
            self.children[keyword] = CommandNode(keyword, help_text, is_placeholder=is_placeholder)
        return self.children[keyword]


def _build_exec_tree() -> CommandNode:
    root = CommandNode("<root>")

    root.add("configure", "Enter configuration mode").add("terminal", "Configure from the terminal")

    show = root.add("show", "Show running system information")
    show.add("interface", "Interface status and configuration").add(
        "brief", "Show a brief summary of interface status"
    )
    iface_show = show.children["interface"]
    iface_show.add("<interface-name>", "Interface name, e.g. fc1/1", is_placeholder=True)
    iface_ph = iface_show.children["<interface-name>"]
    iface_ph.add("transceiver", "Show transceiver/SFP diagnostic information")
    iface_ph.add("trunk", "Show trunk state for this interface")

    show.add("trunk", "Show trunking interfaces")
    show.add("vsan", "Show VSAN information")
    flogi = show.add("flogi", "Show FLOGI information")
    flogi.add("database", "Show FLOGI database")
    zoneset = show.add("zoneset", "Show zoneset information")
    zoneset.add("active", "Show active zoneset").add(
        "vsan", "Specify VSAN"
    ).add("<vsan-id>", "VSAN ID", is_placeholder=True)
    show.add("running-config", "Show current running configuration")
    show.add("startup-config", "Show startup configuration")
    show.add("hardware", "Show hardware inventory")
    show.add("environment", "Show environmental information")
    show.add("logging", "Show logging buffer")

    copy = root.add("copy", "Copy configuration or image files")
    copy.add("running-config", "Copy running configuration").add(
        "startup-config", "Copy to startup configuration"
    )

    write = root.add("write", "Write configuration to nonvolatile memory")
    write.add("erase", "Erase startup configuration")

    root.add("reload", "Reload the switch")
    root.add("exit", "Exit the current mode")

    return root


def _build_config_tree() -> CommandNode:
    root = CommandNode("<root>")

    iface = root.add("interface", "Select an interface to configure")
    iface.add("<interface-name>", "Interface name, e.g. fc1/1 or mgmt0", is_placeholder=True)

    vsan = root.add("vsan", "Configure VSAN parameters")
    vsan.add("database", "Enter VSAN database configuration mode")

    root.add("hostname", "Set the switch hostname").add(
        "<hostname>", "New hostname", is_placeholder=True
    )

    zone = root.add("zone", "Configure a zone")
    zone.add("name", "Zone name").add("<zone-name>", "Zone name", is_placeholder=True).add(
        "vsan", "VSAN for this zone"
    ).add("<vsan-id>", "VSAN ID", is_placeholder=True)

    zoneset = root.add("zoneset", "Configure a zoneset")
    zoneset.add("name", "Zoneset name").add(
        "<zoneset-name>", "Zoneset name", is_placeholder=True
    ).add("vsan", "VSAN for this zoneset").add("<vsan-id>", "VSAN ID", is_placeholder=True)
    zoneset.add("activate", "Activate a zoneset").add(
        "vsan", "VSAN"
    ).add("<vsan-id>", "VSAN ID", is_placeholder=True).add(
        "<zoneset-name>", "Zoneset name to activate", is_placeholder=True
    )

    root.add("end", "Exit to EXEC mode")
    root.add("exit", "Exit to EXEC mode")

    return root


def _build_config_if_tree() -> CommandNode:
    root = CommandNode("<root>")

    root.add("shutdown", "Shutdown the interface")
    no = root.add("no", "Negate a command")
    no.add("shutdown", "Bring up the interface")

    switchport = root.add("switchport", "Configure switchport parameters")
    speed = switchport.add("speed", "Configure interface speed")
    for s in ["1000", "2000", "4000", "8000", "16000", "32000", "64000", "128000", "auto"]:
        speed.add(s, f"Set speed to {s if s == 'auto' else s + ' Mbps'}")

    mode = switchport.add("mode", "Configure port mode")
    for m in ["F", "E", "TE", "auto"]:
        mode.add(m, f"Set port mode to {m}")

    trunk = switchport.add("trunk", "Configure trunk parameters")
    allowed = trunk.add("allowed", "Set allowed VSANs")
    allowed.add("vsan", "VSAN list").add(
        "<vsan-list>", "Comma-separated VSAN IDs, e.g. 1,10,20", is_placeholder=True
    )

    root.add("vsan", "Assign interface to VSAN").add(
        "<vsan-id>", "VSAN ID", is_placeholder=True
    )

    ip = root.add("ip", "Configure IP parameters (mgmt0 only)")
    ip.add("address", "Set IP address").add(
        "<ip-address>", "IP address", is_placeholder=True
    ).add("<subnet-mask>", "Subnet mask", is_placeholder=True)

    root.add("exit", "Exit to config mode")

    return root


def _build_config_vsan_db_tree() -> CommandNode:
    root = CommandNode("<root>")
    vsan = root.add("vsan", "Create/configure a VSAN")
    vsan.add("<vsan-id>", "VSAN ID", is_placeholder=True).add(
        "name", "Assign a name to this VSAN"
    ).add("<vsan-name>", "VSAN name", is_placeholder=True)
    root.add("exit", "Exit to config mode")
    return root


def _build_config_zone_tree() -> CommandNode:
    root = CommandNode("<root>")
    member = root.add("member", "Add a member to this zone")
    member.add("pwwn", "Port WWN member").add(
        "<pwwn>", "Port World Wide Name", is_placeholder=True
    )
    root.add("exit", "Exit to config mode")
    return root


def _build_config_zoneset_tree() -> CommandNode:
    root = CommandNode("<root>")
    root.add("member", "Add a zone to this zoneset").add(
        "<zone-name>", "Zone name", is_placeholder=True
    )
    root.add("exit", "Exit to config mode")
    return root


MODE_TREES: Dict[str, CommandNode] = {
    "exec": _build_exec_tree(),
    "config": _build_config_tree(),
    "config-if": _build_config_if_tree(),
    "config-vsan-db": _build_config_vsan_db_tree(),
    "config-zone": _build_config_zone_tree(),
    "config-zoneset": _build_config_zoneset_tree(),
}


def _walk(root: CommandNode, tokens: List[str]) -> (CommandNode, List[str]):
    """Walk the tree following completed tokens (all but the last, in-progress one).
    Returns (node_reached, remaining_tokens_unconsumed)."""
    node = root
    for tok in tokens:
        matched = None
        if tok in node.children:
            matched = node.children[tok]
        else:
            placeholders = [c for c in node.children.values() if c.is_placeholder]
            if placeholders:
                matched = placeholders[0]
            else:
                exact = [c for k, c in node.children.items() if k == tok]
                if exact:
                    matched = exact[0]
        if matched is None:
            return node, [tok]
        node = matched
    return node, []


def get_word_help(mode: str, tokens: List[str], partial: str):
    """For '<partial>?' -- list keywords at current position starting with partial."""
    root = MODE_TREES.get(mode)
    if root is None:
        return []
    node, remainder = _walk(root, tokens)
    if remainder:
        return []
    candidates = [
        (k, c.help_text) for k, c in node.children.items()
        if not c.is_placeholder and k.startswith(partial)
    ]
    return sorted(candidates)


def get_syntax_help(mode: str, tokens: List[str]):
    """For 'show <space>?' -- list all valid next keywords/placeholders."""
    root = MODE_TREES.get(mode)
    if root is None:
        return []
    node, remainder = _walk(root, tokens)
    if remainder:
        return []
    return sorted([(k, c.help_text) for k, c in node.children.items()])


def complete(mode: str, tokens: List[str], partial: str):
    """Tab completion: returns list of matching keywords for the partial word."""
    root = MODE_TREES.get(mode)
    if root is None:
        return []
    node, remainder = _walk(root, tokens)
    if remainder:
        return []
    matches = [k for k in node.children if not node.children[k].is_placeholder and k.startswith(partial)]
    return sorted(matches)


def resolve_tokens(mode: str, tokens: List[str]) -> List[str]:
    """Expand abbreviated tokens to their full keyword form using the command
    tree, mirroring NX-OS/IOS-style abbreviation (e.g. 'sh int br' ->
    'show interface brief'). Placeholder tokens (interface names, IDs, etc.)
    and tokens with no unambiguous match are passed through unchanged.
    """
    root = MODE_TREES.get(mode)
    if root is None:
        return tokens

    resolved = []
    node = root
    for tok in tokens:
        if tok in node.children:
            resolved.append(tok)
            node = node.children[tok]
            continue

        exact_children = {k: c for k, c in node.children.items() if not c.is_placeholder}
        matches = [k for k in exact_children if k.startswith(tok)]

        if len(matches) == 1:
            full = matches[0]
            resolved.append(full)
            node = node.children[full]
            continue

        placeholders = [c for c in node.children.values() if c.is_placeholder]
        if placeholders:
            resolved.append(tok)
            node = placeholders[0]
            continue

        resolved.append(tok)
        remaining_idx = tokens.index(tok, len(resolved) - 1)
        resolved.extend(tokens[remaining_idx + 1:])
        return resolved

    return resolved
