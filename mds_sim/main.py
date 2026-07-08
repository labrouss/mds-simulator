"""Entrypoint: boots one simulated MDS switch instance
(SSH CLI + NX-API + Fabric Bus + Instructor API).
"""

import os
import time
import threading
import uvicorn

from .config.running_config import RunningConfig
from .config.config_store import ConfigStore
from .hardware.port_state_machine import PortStateMachine
from .hardware.fault_injector import FaultInjector
from .cli.dispatcher import Dispatcher
from .cli.ssh_server import serve_ssh
from .nxapi.app import app as nxapi_app, set_dispatcher as nxapi_set_dispatcher
from .instructor_api.app import app as instructor_app, set_context as instructor_set_context
from .fabric_bus.server import FabricBusServer
from .fabric_bus.client import FabricBusClient


def build_switch(hostname="switch1", bus_port=9000):
    cfg = RunningConfig(hostname=hostname)
    store = ConfigStore(hostname)

    if store.exists():
        cfg.load_dict(store.load())

    state_machines = {
        name: PortStateMachine(port, cfg.event_log)
        for name, port in cfg.chassis.ports.items()
    }
    fault_injector = FaultInjector(cfg.chassis, cfg.event_log, state_machines)
    dispatcher = Dispatcher(cfg, fault_injector, state_machines, store)
    dispatcher.sm = state_machines  # exposed for fabric_bus modules

    bus_server = FabricBusServer(hostname, dispatcher, port=bus_port)
    bus_server.start()

    return dispatcher, fault_injector, bus_server


def connect_peers(dispatcher, hostname):
    """Reads PEER_LINKS env var of the form:
    "fc1/1=switch2:9000,fc1/2=switch3:9000" and connects fabric bus clients.
    Retries until peer is reachable (containers may start out of order).
    """
    peer_links = os.environ.get("PEER_LINKS", "").strip()
    if not peer_links:
        return
    for link in peer_links.split(","):
        local_port, target = link.split("=")
        peer_host, peer_port = target.split(":")
        client = FabricBusClient(hostname, dispatcher, local_port.strip())

        def _connect_with_retry(client=client, peer_host=peer_host, peer_port=int(peer_port)):
            for _ in range(30):
                try:
                    err = client.connect(peer_host, peer_port)
                    if err is None:
                        print(f"Fabric bus connected: {client.local_port_name} -> {peer_host}:{peer_port}")
                        return
                except (ConnectionRefusedError, OSError):
                    pass
                time.sleep(2)
            print(f"Fabric bus failed to connect to {peer_host}:{peer_port}")

        threading.Thread(target=_connect_with_retry, daemon=True).start()


def main():
    hostname = os.environ.get("SWITCH_HOSTNAME", "switch1")
    ssh_port = int(os.environ.get("SSH_PORT", "2222"))
    nxapi_port = int(os.environ.get("NXAPI_PORT", "8443"))
    instructor_port = int(os.environ.get("INSTRUCTOR_PORT", "8000"))
    bus_port = int(os.environ.get("BUS_PORT", "9000"))

    dispatcher, fault_injector, bus_server = build_switch(hostname, bus_port)
    nxapi_set_dispatcher(dispatcher)
    instructor_set_context(dispatcher, fault_injector)

    connect_peers(dispatcher, hostname)

    ssh_thread = threading.Thread(
        target=serve_ssh, args=(dispatcher, "0.0.0.0", ssh_port), daemon=True
    )
    ssh_thread.start()

    instructor_thread = threading.Thread(
        target=lambda: uvicorn.run(instructor_app, host="0.0.0.0", port=instructor_port),
        daemon=True,
    )
    instructor_thread.start()

    print(f"[{hostname}] SSH on :{ssh_port}  NX-API on :{nxapi_port}  "
          f"Instructor API on :{instructor_port}  Fabric bus on :{bus_port}")

    uvicorn.run(nxapi_app, host="0.0.0.0", port=nxapi_port)


if __name__ == "__main__":
    main()
