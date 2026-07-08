"""Message schema exchanged between simulator instances over an E-port link.

Simplified stand-in for real FC ELP/domain-merge exchanges: JSON messages
over TCP, one connection per E-port link.
"""

import json

MSG_HELLO = "HELLO"                # initial handshake, exchange switch identity
MSG_ELP = "ELP"                    # exchange link parameters (speed, wwn)
MSG_ELP_ACK = "ELP_ACK"
MSG_DOMAIN_MERGE = "DOMAIN_MERGE"  # exchange domain id + vsan list
MSG_DOMAIN_ACK = "DOMAIN_ACK"
MSG_VSAN_SYNC = "VSAN_SYNC"        # push local vsan/zone state to peer
MSG_LINK_DOWN = "LINK_DOWN"        # peer reports its side went down
MSG_KEEPALIVE = "KEEPALIVE"


def build(msg_type, **kwargs):
    payload = {"type": msg_type}
    payload.update(kwargs)
    return (json.dumps(payload) + "\n").encode("utf-8")


def parse(raw_line: bytes):
    try:
        return json.loads(raw_line.decode("utf-8").strip())
    except Exception:
        return None
