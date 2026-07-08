"""Fabric bus client: initiates an E-port connection to a peer switch instance."""

import socket
import threading
from . import protocol as p


class FabricBusClient:
    def __init__(self, switch_name, dispatcher, local_port_name):
        self.switch_name = switch_name
        self.dispatcher = dispatcher
        self.local_port_name = local_port_name
        self._sock = None
        self._connected = False

    def connect(self, peer_host, peer_port=9000):
        cfg = self.dispatcher.cfg
        port = cfg.chassis.ports[self.local_port_name]
        if port.port_mode not in ("E", "TE"):
            return "% Port must be mode E or TE to connect fabric bus"

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((peer_host, peer_port))
        self._connected = True

        self.dispatcher.sm[self.local_port_name].link_signal_detected()
        self._sock.sendall(p.build(
            p.MSG_HELLO,
            switch_name=self.switch_name,
            target_local_port=self.local_port_name,
        ))

        t = threading.Thread(target=self._recv_loop, daemon=True)
        t.start()
        return None

    def _recv_loop(self):
        buf = b""
        cfg = self.dispatcher.cfg
        sm = self.dispatcher.sm[self.local_port_name]
        try:
            while True:
                data = self._sock.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    msg = p.parse(line + b"\n")
                    if not msg:
                        continue
                    self._handle(msg)
        finally:
            sm.link_lost()
            self._connected = False

    def _handle(self, msg):
        cfg = self.dispatcher.cfg
        sm = self.dispatcher.sm[self.local_port_name]
        port = cfg.chassis.ports[self.local_port_name]

        if msg["type"] == p.MSG_ELP:
            peer_vsans = msg.get("vsans", [1])
            common = sorted(set(port.trunk_allowed_vsans) & set(peer_vsans))
            domain = cfg.domain_mgr.assign_domain(1)
            self._sock.sendall(p.build(
                p.MSG_DOMAIN_MERGE, domain=domain, common_vsans=common,
                vsans=port.trunk_allowed_vsans
            ))
            sm.elp_success(peer_domain=domain, common_vsans=common, peer_vsans=peer_vsans)

        elif msg["type"] == p.MSG_DOMAIN_MERGE:
            common = msg.get("common_vsans", [])
            peer_vsans = msg.get("vsans", common)
            sm.elp_success(peer_domain=msg["domain"], common_vsans=common, peer_vsans=peer_vsans)
            self._sock.sendall(p.build(p.MSG_DOMAIN_ACK))

        elif msg["type"] == p.MSG_LINK_DOWN:
            sm.link_lost()
