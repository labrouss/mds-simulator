# Instructor Dashboard

React + Vite web dashboard for controlling the MDS simulator instructor API.

## Features
- Live WebSocket updates from each switch
- Per-port fault injection: unplug/insert SFP, flap link, degrade signal
- Chassis faults: fail PSU1/PSU2, fail fan
- Live event log stream per switch
- Multi-switch view: add as many switch panels as needed

## Development

```bash
cd instructor_dashboard
npm install
npm run dev
```

Open the local Vite URL shown in the terminal (normally http://localhost:5173).

## Default switch targets
The UI starts with:
- Switch 1 -> localhost:8000
- Switch 2 -> localhost:8001

For the provided Docker Compose lab, update/add switches to:
- switch1 instructor API -> localhost:18001
- switch2 instructor API -> localhost:18002

The dashboard talks to:
- WebSocket: `ws://HOST:PORT/ws`
- REST API: `http://HOST:PORT/faults/...`

## Production build

```bash
npm run build
npm run preview
```

## Build output

Run `npm run build` to generate `dist/`. The instructor API will serve that build at `/` when `instructor_dashboard/dist` exists.
