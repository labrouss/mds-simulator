"""FC ASIC port state machine.

Models the realistic bring-up sequence of a Fibre Channel port,
distinct from a simple up/down Ethernet-style model.
"""

from enum import Enum
from ..logging_.event_log import EventLog


class PortState(str, Enum):
    OFFLINE = "OFFLINE"
    LINK_DOWN = "LINK_DOWN"
    INITIALIZING = "INITIALIZING"
    FLOGI_PENDING = "FLOGI_PENDING"
    ELP_NEGOTIATE = "ELP_NEGOTIATE"
    DOMAIN_MERGE = "DOMAIN_MERGE"
    UP = "UP"
    TRUNKING = "TRUNKING"
    ERR_DISABLED = "ERR_DISABLED"


class PortStateMachine:
    def __init__(self, port, event_log: EventLog):
        self.port = port
        self.log = event_log

    def _set(self, new_state: PortState, msg: str = None):
        old = self.port.oper_state
        self.port.oper_state = new_state.value
        if msg:
            self.log.emit(msg)
        return old, new_state.value

    def admin_up(self):
        p = self.port
        p.admin_state = "up"
        if not p.sfp_present:
            return self._set(PortState.OFFLINE,
                f"%PORT-5-IF_DOWN_SFP_ABSENT: Interface {p.name} down (SFP not present)")
        return self._set(PortState.LINK_DOWN,
            f"%PORT-5-IF_ADMIN_UP: Interface {p.name} admin up, waiting for link")

    def admin_down(self):
        p = self.port
        p.admin_state = "down"
        p.negotiated_speed = None
        return self._set(PortState.OFFLINE,
            f"%PORT-5-IF_DOWN_ADMIN_DOWN: Interface {p.name} is down (Administratively down)")

    def link_signal_detected(self):
        """Called by fault injector / peer link connect event."""
        p = self.port
        if p.admin_state != "up" or not p.sfp_present:
            return
        self._set(PortState.INITIALIZING,
            f"%PORT-5-SPEED_NEGOTIATE: Interface {p.name} negotiating speed/word sync")
        if p.port_mode in ("F", "auto"):
            self._set(PortState.FLOGI_PENDING,
                f"%PORT-5-IF_UP: Interface {p.name} link up, waiting for FLOGI")
        elif p.port_mode in ("E", "TE"):
            self._set(PortState.ELP_NEGOTIATE,
                f"%PORT-5-ELP: Interface {p.name} exchanging link parameters (ELP)")

    def flogi_received(self, wwn: str):
        p = self.port
        if p.oper_state != PortState.FLOGI_PENDING.value:
            return
        p.peer_wwn = wwn
        self._set(PortState.UP,
            f"%FLOGI-5-FLOGI_ACCEPT: FLOGI accepted from {wwn} on {p.name}")

    def elp_success(self, peer_domain: int, common_vsans=None, peer_vsans=None):
        p = self.port
        self._set(PortState.DOMAIN_MERGE,
            f"%FSPF-5-DOMAIN_MERGE: Merging domain with peer domain {peer_domain} on {p.name}")
        p.domain_id = peer_domain

        if p.port_mode == "TE":
            common_vsans = common_vsans or []
            peer_vsans = peer_vsans if peer_vsans is not None else common_vsans
            p.negotiated_trunk_vsans = common_vsans

            # Per-VSAN trunk state: a locally-allowed VSAN is 'up' only if the
            # peer also allows it; otherwise it's 'isolated' on this trunk,
            # mirroring real per-VSAN TE-port trunk behavior.
            vsan_status = {}
            for v in p.trunk_allowed_vsans:
                vsan_status[v] = "up" if v in common_vsans else "isolated"
            p.vsan_trunk_status = vsan_status

            if not common_vsans:
                p.trunk_isolated_reason = "no common VSANs with peer"
                self._set(PortState.ERR_DISABLED,
                    f"%PORT-4-TRUNK_ISOLATED: Interface {p.name} isolated, no VSANs in common with peer")
                return

            p.trunk_isolated_reason = None
            isolated_vsans = [v for v, s in vsan_status.items() if s == "isolated"]
            self._set(PortState.TRUNKING,
                f"%PORT-5-IF_UP: Interface {p.name} is up in mode TE, trunking vsans {common_vsans}")
            if isolated_vsans:
                self.log.emit(
                    f"%PORT-4-VSAN_ISOLATED: VSAN(s) {isolated_vsans} isolated on trunk {p.name} "
                    f"(not allowed on peer)"
                )
        else:
            self._set(PortState.UP,
                f"%PORT-5-IF_UP: Interface {p.name} is up in mode {p.port_mode}")

    def link_lost(self):
        p = self.port
        p.peer_wwn = None
        p.negotiated_speed = None
        self._set(PortState.LINK_DOWN,
            f"%PORT-5-IF_DOWN_LINK_FAILURE: Interface {p.name} down (Link failure)")
        p.counters["link_failures"] += 1

    def error_disable(self, reason: str):
        p = self.port
        p.error_disabled_reason = reason
        self._set(PortState.ERR_DISABLED,
            f"%PORT-4-ERR_DISABLE: Interface {p.name} err-disabled, reason: {reason}")
