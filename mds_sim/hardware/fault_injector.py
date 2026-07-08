"""Fault injection API used by instructors/tests to simulate hardware events."""

from .port_state_machine import PortStateMachine


class FaultInjector:
    def __init__(self, chassis, event_log, state_machines):
        self.chassis = chassis
        self.log = event_log
        self.sm = state_machines  # dict port_name -> PortStateMachine

    def unplug_sfp(self, port_name):
        port = self.chassis.ports[port_name]
        port.remove_sfp()
        self.sm[port_name].link_lost()
        self.log.emit(f"%PORT-5-IF_DOWN_SFP_ABSENT: Interface {port_name} down (SFP not present)")

    def insert_sfp(self, port_name, sfp_type="16G_SW"):
        port = self.chassis.ports[port_name]
        port.insert_sfp(sfp_type)
        if port.admin_state == "up":
            self.sm[port_name].link_signal_detected()

    def connect_link(self, port_name):
        self.sm[port_name].link_signal_detected()

    def flap_link(self, port_name):
        self.sm[port_name].link_lost()

    def degrade_signal(self, port_name):
        port = self.chassis.ports[port_name]
        port.counters["crc_errors"] += 50
        self.log.emit(f"%PORT-4-CRC_ERR: Excessive CRC errors detected on {port_name}")

    def fail_psu(self, psu_num=1):
        if psu_num == 1:
            self.chassis.environment.psu1_ok = False
        else:
            self.chassis.environment.psu2_ok = False
        self.log.emit(f"%PLATFORM-2-PS_FAIL: Power supply {psu_num} failed")

    def fail_fan(self):
        self.chassis.environment.fans_ok = False
        self.log.emit("%PLATFORM-2-FAN_FAIL: Fan module failure detected")
