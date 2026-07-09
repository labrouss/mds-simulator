"""Basic sanity tests for the MDS simulator core logic."""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mds_sim.config.running_config import RunningConfig
from mds_sim.config.config_store import ConfigStore
from mds_sim.hardware.port_state_machine import PortStateMachine
from mds_sim.hardware.fault_injector import FaultInjector
from mds_sim.cli.dispatcher import Dispatcher
from mds_sim.fabric_bus.server import FabricBusServer
from mds_sim.fabric_bus.client import FabricBusClient


def build(hostname, bus_port, base_dir="test_configs"):
    cfg = RunningConfig(hostname=hostname)
    store = ConfigStore(hostname, base_dir=base_dir)
    sms = {name: PortStateMachine(p, cfg.event_log) for name, p in cfg.chassis.ports.items()}
    fi = FaultInjector(cfg.chassis, cfg.event_log, sms)
    d = Dispatcher(cfg, fi, sms, store)
    d.sm = sms
    server = FabricBusServer(hostname, d, port=bus_port)
    server.start()
    return d


def test_f_port_bring_up():
    d = build("t1", 9501)
    d.execute("configure terminal")
    d.execute("interface fc1/1")
    d.execute("switchport mode F")
    d.execute("exit")
    d.execute("exit")
    d.fi.insert_sfp("fc1/1", "16G_SW")
    d.execute("configure terminal")
    d.execute("interface fc1/1")
    d.execute("no shutdown")
    d.execute("exit")
    d.execute("exit")
    assert d.cfg.chassis.ports["fc1/1"].oper_state == "FLOGI_PENDING"


def test_speed_rejects_unsupported():
    d = build("t2", 9502)
    d.fi.insert_sfp("fc1/1", "8G_SW")
    d.execute("configure terminal")
    d.execute("interface fc1/1")
    result = d.execute("switchport speed 32000")
    assert "IF_INVALID_SPEED" in result


def test_config_persistence_roundtrip():
    d = build("t3", 9503)
    d.execute("configure terminal")
    d.execute("hostname persisttest")
    d.execute("exit")
    d.execute("copy running-config startup-config")
    assert d.store.exists()
    data = d.store.load()
    assert data["hostname"] == "persisttest"


def test_eport_trunk_matching_vsans():
    d1 = build("t4a", 9504)
    d2 = build("t4b", 9505)
    for d, vsans in [(d1, "1,10"), (d2, "1,10")]:
        d.execute("configure terminal")
        d.execute("interface fc1/1")
        d.execute("switchport mode TE")
        d.execute(f"switchport trunk allowed vsan {vsans}")
        d.execute("no shutdown")
        d.execute("exit")
        d.execute("exit")
    c = FabricBusClient("t4b", d2, "fc1/1")
    c.connect("127.0.0.1", 9504)
    time.sleep(1)
    assert d1.cfg.chassis.ports["fc1/1"].oper_state == "TRUNKING"
    assert sorted(d1.cfg.chassis.ports["fc1/1"].negotiated_trunk_vsans) == [1, 10]


def test_eport_trunk_partial_overlap_isolation():
    d1 = build("t5a", 9506)
    d2 = build("t5b", 9507)
    for d, vsans in [(d1, "1,10,20"), (d2, "1,40")]:
        d.execute("configure terminal")
        d.execute("interface fc1/1")
        d.execute("switchport mode TE")
        d.execute(f"switchport trunk allowed vsan {vsans}")
        d.execute("no shutdown")
        d.execute("exit")
        d.execute("exit")
    c = FabricBusClient("t5b", d2, "fc1/1")
    c.connect("127.0.0.1", 9506)
    time.sleep(1)
    port = d1.cfg.chassis.ports["fc1/1"]
    assert port.oper_state == "TRUNKING"
    assert port.vsan_trunk_status[10] == "isolated"
    assert port.vsan_trunk_status[1] == "up"


def test_eport_no_overlap_err_disabled():
    d1 = build("t6a", 9508)
    d2 = build("t6b", 9509)
    for d, vsans in [(d1, "30"), (d2, "40")]:
        d.execute("configure terminal")
        d.execute("interface fc1/1")
        d.execute("switchport mode TE")
        d.execute(f"switchport trunk allowed vsan {vsans}")
        d.execute("no shutdown")
        d.execute("exit")
        d.execute("exit")
    c = FabricBusClient("t6b", d2, "fc1/1")
    c.connect("127.0.0.1", 9508)
    time.sleep(1)
    assert d1.cfg.chassis.ports["fc1/1"].oper_state == "ERR_DISABLED"




def test_abbreviation_unambiguous_resolves():
    d = build("t7", 9510)
    result = d.execute("sh int br")
    assert "Interface" in result and "Vsan" in result


def test_abbreviation_mode_navigation():
    d = build("t8", 9511)
    d.execute("conf t")
    assert d.ctx.mode == "config"
    d.execute("int fc1/1")
    assert d.ctx.mode == "config-if"
    d.execute("no shut")
    assert d.cfg.chassis.ports["fc1/1"].admin_state == "up"
    d.execute("ex")
    assert d.ctx.mode == "config"
    d.execute("end")
    assert d.ctx.mode == "exec"


def test_ambiguous_abbreviation_rejected():
    d = build("t9", 9512)
    result = d.execute("c terminal")
    assert "Invalid" in result
    assert d.ctx.mode == "exec"


if __name__ == "__main__":
    test_f_port_bring_up()
    test_speed_rejects_unsupported()
    test_config_persistence_roundtrip()
    test_eport_trunk_matching_vsans()
    test_eport_trunk_partial_overlap_isolation()
    test_eport_no_overlap_err_disabled()
    test_abbreviation_unambiguous_resolves()
    test_abbreviation_mode_navigation()
    test_ambiguous_abbreviation_rejected()
    print("ALL TESTS PASSED")
