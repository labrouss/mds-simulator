"""Paramiko-based SSH server exposing the CLI dispatcher interactively."""

import socket
import threading
import paramiko

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
                elif ch == "\x7f":  # backspace
                    if buf:
                        buf = buf[:-1]
                        channel.send("\b \b")
                else:
                    buf += ch
                    channel.send(ch)
    finally:
        try:
            channel.close()
        except Exception:
            pass


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
