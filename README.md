# Cisco MDS 9000 CLI & NX-API Educational Simulator

A Python-based simulator of a Cisco MDS 9000 Fibre Channel switch, built for
educational/training purposes. It exposes:

- An **SSH CLI** (Paramiko) that mimics real NX-OS command syntax, modes,
  and `show` command output formatting.
- An **NX-API** HTTP endpoint (FastAPI) matching Cisco's real `ins_api`
  JSON envelope, so real automation scripts (Ansible, pyATS, requests)
  can target it unmodified.
- A **hardware/ASIC simulation layer**: SFP-dependent speed negotiation
  (4G-128G), a realistic FC port state machine (FLOGI for F-ports,
  ELP/domain-merge for E/TE-ports), environmental sensors, and a fault
  injector for simulating hardware issues.
- A **fabric layer**: VSANs, zoning/zonesets, FLOGI/FCNS database, domain
  ID management.
- A **fabric bus** protocol allowing multiple simulator instances (e.g.
  Docker containers) to connect their E-ports/TE-ports and merge into a
  simulated multi-switch SAN fabric, including realistic per-VSAN trunk
  isolation behavior.
- An **instructor REST API**, separate from student-facing interfaces,
  for live fault injection (unplug SFP, flap link, fail PSU/fan, etc.)
  during a lab session.
- **Persistent configuration**: running-config vs startup-config, with
  `copy running-config startup-config`, `write erase`, and `reload`.

## Quick Start (single switch, local)

```bash
pip install -r requirements.txt
python -m mds_sim.main
```

Then in another terminal:

```bash
ssh admin@localhost -p 2222   # password: admin
```

NX-API:

```bash
curl -X POST http://localhost:8443/ins \
  -H "Content-Type: application/json" \
  -d '{"ins_api": {"type": "cli_show", "input": "show interface brief"}}'
```

Instructor fault injection:

```bash
curl -X POST http://localhost:8000/faults/unplug_sfp \
  -H "Content-Type: application/json" -d '{"port": "fc1/1"}'
```

## Two-Switch Fabric Lab (Docker Compose)

```bash
docker compose up --build
```

This brings up `switch1` and `switch2` on an internal bridge network.
`switch1` is configured (via `PEER_LINKS` env var) to connect its fc1/1
fabric-bus client out to `switch2`'s fabric-bus server automatically once
both containers are running.

SSH into each:

```bash
ssh admin@localhost -p 12221   # switch1
ssh admin@localhost -p 12222   # switch2
```

Configure fc1/1 as a trunking E-port on both switches to see them merge:

```
configure terminal
interface fc1/1
switchport mode TE
switchport trunk allowed vsan 1,10,20
no shutdown
exit
exit
show interface fc1/1 trunk
```

See `examples/sample_labs/` for guided exercises.

## Project Layout

See `mds_sim/` subpackages: `hardware/`, `fabric/`, `fabric_bus/`,
`config/`, `cli/`, `nxapi/`, `instructor_api/`, `logging_/`.

## Notes

This is an educational approximation, not a byte-accurate FC protocol
implementation. Framing, real FLOGI/PLOGI exchanges, FSPF routing, and
zoning enforcement are simplified for teaching clarity while preserving
realistic CLI syntax, state transitions, and failure modes.


## Instructor Dashboard

A React/Vite instructor dashboard is included under `instructor_dashboard/`. It connects to each switch's instructor API over WebSocket for live port/log updates and uses the REST endpoints for fault injection. See `instructor_dashboard/README.md` for setup.


The instructor API serves the built dashboard at `/` when `instructor_dashboard/dist` is present. Run `cd instructor_dashboard && npm run build` before starting the simulator if you want the web UI on the instructor port.
