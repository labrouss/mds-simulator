"""Pydantic-free simple schema helpers matching Cisco NX-API ins_api envelope."""


def wrap_response(cmd_input: str, body, msg="Success", code="200"):
    return {
        "ins_api": {
            "outputs": {
                "output": {
                    "body": body,
                    "input": cmd_input,
                    "msg": msg,
                    "code": code,
                }
            }
        }
    }


def wrap_error(cmd_input: str, msg, code="400"):
    return wrap_response(cmd_input, {}, msg=msg, code=code)
