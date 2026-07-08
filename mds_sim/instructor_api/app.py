"""Instructor-facing REST API for live fault injection and state inspection.

Kept separate from the student-facing SSH/NX-API so labs can be scripted
or triggered live without touching the student session.
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MDS Simulator Instructor API")

_fault_injector = None
_dispatcher = None


def set_context(dispatcher, fault_injector):
    global _dispatcher, _fault_injector
    _dispatcher = dispatcher
    _fault_injector = fault_injector


class SFPRequest(BaseModel):
    port: str
    sfp_type: str = "16G_SW"


class PortRequest(BaseModel):
    port: str


@app.post("/faults/unplug_sfp")
def unplug_sfp(req: PortRequest):
    _fault_injector.unplug_sfp(req.port)
    return {"status": "ok"}


@app.post("/faults/insert_sfp")
def insert_sfp(req: SFPRequest):
    _fault_injector.insert_sfp(req.port, req.sfp_type)
    return {"status": "ok"}


@app.post("/faults/flap_link")
def flap_link(req: PortRequest):
    _fault_injector.flap_link(req.port)
    return {"status": "ok"}


@app.post("/faults/degrade_signal")
def degrade_signal(req: PortRequest):
    _fault_injector.degrade_signal(req.port)
    return {"status": "ok"}


@app.post("/faults/fail_psu/{psu_num}")
def fail_psu(psu_num: int):
    _fault_injector.fail_psu(psu_num)
    return {"status": "ok"}


@app.post("/faults/fail_fan")
def fail_fan():
    _fault_injector.fail_fan()
    return {"status": "ok"}


@app.get("/state/ports")
def get_ports():
    return {name: p.brief_row() for name, p in _dispatcher.cfg.chassis.ports.items()}


@app.get("/state/logging")
def get_logging():
    return {"events": _dispatcher.cfg.event_log.tail(50)}
