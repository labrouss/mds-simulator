"""Paramiko-based SSH server exposing the CLI dispatcher interactively,
with context-sensitive help ('?') and Tab-completion matching real NX-OS
CLI behavior.
"""

import socket
import threading
import paramiko

from . import command_tree as ct

HOST_KEY = paramiko.RSAKey.generate(2048)


class SSHServerInterface(paramiko.ServerInterface):
    def __init__(self, username="admin", password="admin"):
        self.username = username
        self.password = password
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == self.username and password == self.password:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, *args, **kwargs):
        return True


def _tokens_and_partial(buf: str):
    """Split buffer into completed tokens and the in-progress partial word."""
    if buf.endswith(" "):
        return buf.strip().split(), ""
    parts = buf.split()
    if not parts:
        return [], ""
    return parts[:-1], parts[-1]


def _format_help_lines(candidates):
    if not candidates:
        return "% No matching commands"
    width = max(len(k) for k, _ in candidates) + 2
    lines = []
    for k, h in candidates:
        lines.append(f"  {k:<{width}}{h}")
    return "\r\n".join(lines)


def handle_client(client_sock, dispatcher, username="admin", password="admin"):
    transport = paramiko.Transport(client_sock)
    transport.add_server_key(HOST_KEY)
    server = SSHServerInterface(username, password)
    transport.start_server(server=server)

    channel = transport.accept(20)
    if channel is None:
        return
    server.event.wait(10)

    banner = f"Cisco MDS Simulator ({dispatcher.cfg.hostname})\r\n"
    channel.send(banner)
    channel.send(dispatcher.ctx.prompt())

    buf = ""
    try:
        while True:
            data = channel.recv(1024)
            if not data:
                break
            text = data.decode("utf-8", errors="ignore")
            for ch in text:
                if ch in ("\r", "\n"):
                    channel.send("\r\n")
                    line = buf.strip()
                    buf = ""
                    if line in ("exit", "quit") and dispatcher.ctx.mode == "exec":
                        channel.send("Connection closed.\r\n")
                        channel.close()
                        return
                    output = dispatcher.execute(line)
                    if output:
                        channel.send(output.replace("\n", "\r\n") + "\r\n")
                    channel.send(dispatcher.ctx.prompt())

                elif ch == "\x7f" or ch == "\x08":  # backspace
                    if buf:
                        buf = buf[:-1]
                        channel.send("\b \b")

                elif ch == "?":
                    mode = dispatcher.ctx.mode
                    tokens, partial = _tokens_and_partial(buf)
                    channel.send("?\r\n")
                    if partial:
                        candidates = ct.get_word_help(mode, tokens, partial)
                    else:
                        candidates = ct.get_syntax_help(mode, tokens)
                    channel.send(_format_help_lines(candidates) + "\r\n")
                    channel.send(dispatcher.ctx.prompt() + buf)

                elif ch == "\t":
                    mode = dispatcher.ctx.mode
                    tokens, partial = _tokens_and_partial(buf)
                    if not partial:
                        continue
                    matches = ct.complete(mode, tokens, partial)
                    if len(matches) == 1:
                        completion = matches[0][len(partial):]
                        buf += completion + " "
                        channel.send(completion + " ")
                    elif len(matches) > 1:
                        common = _common_prefix(matches)
                        if len(common) > len(partial):
                            extra = common[len(partial):]
                            buf += extra
                            channel.send(extra)
                        else:
                            channel.send("\r\n")
                            channel.send(_format_help_lines([(m, "") for m in matches]) + "\r\n")
                            channel.send(dispatcher.ctx.prompt() + buf)

                else:
                    buf += ch
                    channel.send(ch)
    finally:
        try:
            channel.close()
        except Exception:
            pass


def _common_prefix(strings):
    if not strings:
        return ""
    prefix = strings[0]
    for s in strings[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


def serve_ssh(dispatcher, bind_addr="0.0.0.0", port=2222, username="admin", password="admin"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_addr, port))
    sock.listen(5)
    print(f"SSH simulator listening on {bind_addr}:{port}")
    while True:
        client, addr = sock.accept()
        t = threading.Thread(
            target=handle_client, args=(client, dispatcher, username, password), daemon=True
        )
        t.start()
