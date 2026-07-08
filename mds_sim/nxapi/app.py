"""FastAPI NX-API endpoint mirroring Cisco's real ins_api schema.

POST /ins with body:
{
  "ins_api": {
    "type": "cli_show" | "cli_conf",
    "input": "show interface brief",
    "output_format": "json"
  }
}
"""

from fastapi import FastAPI, Request
from .schema import wrap_response, wrap_error

app = FastAPI(title="MDS NX-API Simulator")

_dispatcher = None  # injected at startup via set_dispatcher()


def set_dispatcher(dispatcher):
    global _dispatcher
    _dispatcher = dispatcher


@app.post("/ins")
async def nxapi(request: Request):
    payload = await request.json()
    try:
        ins = payload["ins_api"]
        cmd_input = ins["input"]
    except (KeyError, TypeError):
        return wrap_error("", "Malformed request")

    if _dispatcher is None:
        return wrap_error(cmd_input, "Simulator not initialized")

    commands = cmd_input.split(" ; ") if " ; " in cmd_input else [cmd_input]
    outputs = []
    for cmd in commands:
        result = _dispatcher.execute(cmd)
        outputs.append(result)

    body = outputs[0] if len(outputs) == 1 else outputs
    return wrap_response(cmd_input, body)
