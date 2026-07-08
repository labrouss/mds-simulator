"""Fabric bus server: accepts inbound E-port connections from peer switches.

Each accepted connection corresponds to one local E-port. The remote peer
must specify which local port it is connecting to in its HELLO message.
"""

import socket
import threading
from . import protocol as p


class FabricBusServer:
    def __init__(self, switch_name, dispatcher, port=9000):
        self.switch_name = switch_name
        self.dispatcher = dispatcher
        self.port = port
        self._sock = None

    def start(self, bind_addr="0.0.0.0"):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((bind_addr, self.port))
        self._sock.listen(5)
        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        return t

    def _accept_loop(self):
        while True:
            conn, addr = self._sock.accept()
            threading.Thread(
                target=self._handle_conn, args=(conn,), daemon=True
            ).start()

    def _handle_conn(self, conn):
        buf = b""
        local_port_name = None
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    msg = p.parse(line + b"\n")
                    if not msg:
                        continue
                    local_port_name = self._process(conn, msg, local_port_name)
        finally:
            if local_port_name:
                self._on_disconnect(local_port_name)
            conn.close()

    def _process(self, conn, msg, local_port_name):
        cfg = self.dispatcher.cfg
        sm_map = self.dispatcher.sm

        if msg["type"] == p.MSG_HELLO:
            local_port_name = msg["target_local_port"]
            port = cfg.chassis.ports.get(local_port_name)
            if not port or port.port_mode not in ("E", "TE"):
                conn.sendall(p.build(p.MSG_LINK_DOWN, reason="not_eport"))
                return None
            sm_map[local_port_name].link_signal_detected()
            conn.sendall(p.build(
                p.MSG_ELP,
                switch_name=self.switch_name,
                port=local_port_name,
                vsans=port.trunk_allowed_vsans,
            ))
            return local_port_name

        if msg["type"] == p.MSG_ELP and local_port_name:
            port = cfg.chassis.ports[local_port_name]
            peer_vsans = msg.get("vsans", [1])
            common = sorted(set(port.trunk_allowed_vsans) & set(peer_vsans))
            domain = cfg.domain_mgr.assign_domain(1)
            conn.sendall(p.build(
                p.MSG_DOMAIN_MERGE, domain=domain, common_vsans=common,
                vsans=port.trunk_allowed_vsans
            ))
            sm_map[local_port_name].elp_success(
                peer_domain=domain, common_vsans=common, peer_vsans=peer_vsans
            )
            return local_port_name

        if msg["type"] == p.MSG_DOMAIN_MERGE and local_port_name:
            common = msg.get("common_vsans", [])
            peer_vsans = msg.get("vsans", common)
            sm_map[local_port_name].elp_success(
                peer_domain=msg["domain"], common_vsans=common, peer_vsans=peer_vsans
            )
            conn.sendall(p.build(p.MSG_DOMAIN_ACK))
            return local_port_name

        if msg["type"] == p.MSG_VSAN_SYNC and local_port_name:
            for vsan in msg.get("vsans", []):
                cfg.vsan_db.create(vsan["vsan"], vsan.get("name", ""))
            return local_port_name

        return local_port_name

    def _on_disconnect(self, local_port_name):
        sm = self.dispatcher.sm.get(local_port_name)
        if sm:
            sm.link_lost()
