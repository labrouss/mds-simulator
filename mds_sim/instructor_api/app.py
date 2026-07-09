"""Instructor-facing REST + WebSocket API for live fault injection,
state inspection, and real-time dashboard updates.
"""

import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="MDS Simulator Instructor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_fault_injector = None
_dispatcher = None
_ws_clients = set()
_loop = None


def _dashboard_dir():
    here = Path(__file__).resolve()
    candidate = here.parents[2] / "instructor_dashboard" / "dist"
    return candidate if candidate.exists() else None


def mount_dashboard():
    d = _dashboard_dir()
    if d is not None:
        try:
            app.mount("/assets", StaticFiles(directory=str(d / "assets")), name="assets")
        except Exception:
            pass
        @app.get("/")
        def root_index():
            return FileResponse(str(d / "index.html"))


def set_context(dispatcher, fault_injector):
    global _dispatcher, _fault_injector, _loop
    _dispatcher = dispatcher
    _fault_injector = fault_injector
    try:
        _loop = asyncio.get_event_loop()
    except RuntimeError:
        _loop = None
    dispatcher.cfg.event_log.subscribe(_on_new_event)
    mount_dashboard()


def _on_new_event(entry: str):
    _broadcast_soon({"type": "log", "message": entry})
    _broadcast_soon({"type": "ports", "ports": _ports_snapshot()})


def _ports_snapshot():
    if _dispatcher is None:
        return {}
    return {name: p.brief_row() for name, p in _dispatcher.cfg.chassis.ports.items()}


def _broadcast_soon(payload: dict):
    if _loop is None or not _ws_clients:
        return
    try:
        asyncio.run_coroutine_threadsafe(_broadcast(payload), _loop)
    except Exception:
        pass


async def _broadcast(payload: dict):
    data = json.dumps(payload)
    dead = []
    for ws in list(_ws_clients):
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.discard(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global _loop
    _loop = asyncio.get_event_loop()
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "init",
            "hostname": _dispatcher.cfg.hostname if _dispatcher else "unknown",
            "ports": _ports_snapshot(),
            "logs": _dispatcher.cfg.event_log.tail(50) if _dispatcher else [],
        }))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)


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
    return _ports_snapshot()


@app.get("/state/logging")
def get_logging():
    return {"events": _dispatcher.cfg.event_log.tail(50)}


@app.get("/state/hostname")
def get_hostname():
    return {"hostname": _dispatcher.cfg.hostname if _dispatcher else "unknown"}
