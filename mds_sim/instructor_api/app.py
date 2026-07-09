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


class PortConfigRequest(BaseModel):
    port: str
    mode: str | None = None            # F, E, TE, auto
    vsan: int | None = None            # assign interface to vsan (F-port typical)
    speed: str | None = None           # 1000..128000 or auto
    trunk_allowed_vsan: str | None = None  # e.g. "1,10,20"
    admin_state: str | None = None     # "up" or "down"


def _run_config_lines(lines):
    if _dispatcher is None:
        return {"status": "error", "message": "dispatcher not ready"}
    _dispatcher.execute("configure terminal")
    outputs = []
    for line in lines:
        outputs.append(_dispatcher.execute(line))
    _dispatcher.execute("exit")
    _dispatcher.execute("exit")
    return {"status": "ok", "output": [o for o in outputs if o]}


@app.post("/config/port")
def config_port(req: PortConfigRequest):
    lines = [f"interface {req.port}"]
    if req.mode:
        lines.append(f"switchport mode {req.mode}")
    if req.speed:
        lines.append(f"switchport speed {req.speed}")
    if req.trunk_allowed_vsan:
        lines.append(f"switchport trunk allowed vsan {req.trunk_allowed_vsan}")
    if req.vsan is not None:
        lines.append(f"vsan {req.vsan}")
    if req.admin_state == "up":
        lines.append("no shutdown")
    elif req.admin_state == "down":
        lines.append("shutdown")
    return _run_config_lines(lines)


@app.get("/config/port/{port_name}")
def get_port_config(port_name: str):
    if _dispatcher is None:
        return {}
    p = _dispatcher.cfg.chassis.ports.get(port_name)
    if p is None:
        return {"error": "port not found"}
    return {
        "name": p.name,
        "port_mode": getattr(p, "port_mode", None),
        "vsan": getattr(p, "vsan", None),
        "speed_config": getattr(p, "speed_config", None),
        "negotiated_speed": getattr(p, "negotiated_speed", None),
        "admin_state": getattr(p, "admin_state", None),
        "oper_state": getattr(p, "oper_state", None),
        "trunk_allowed_vsans": getattr(p, "trunk_allowed_vsans", None),
    }


@app.get("/debug/routes")
def debug_routes():
    routes = []
    for r in app.routes:
        routes.append(getattr(r, "path", str(r)))
    return {"routes": routes, "dashboard_dir": str(_dashboard_dir()) if _dashboard_dir() else None}


@app.get("/favicon.ico")
def favicon():
    d = _dashboard_dir()
    if d is not None:
        ico = d / "favicon.ico"
        if ico.exists():
            return FileResponse(str(ico))
    return {"status": "ok"}


@app.get("/state/full")
def get_full_state():
    return {
        "hostname": _dispatcher.cfg.hostname if _dispatcher else "unknown",
        "ports": _ports_snapshot(),
        "logs": _dispatcher.cfg.event_log.tail(50) if _dispatcher else [],
    }
