#!/usr/bin/env python3
"""Ping server: receives ping requests from clients and returns results."""

import socket
import subprocess
import json
import threading
import argparse
import platform

HOST = "0.0.0.0"
PORT = 9999


def run_ping(target: str, count: int = 4) -> dict:
    flag = "-n" if platform.system() == "Windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", flag, str(count), target],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout or result.stderr,
            "target": target,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Ping timed out.", "target": target}
    except FileNotFoundError:
        return {"success": False, "output": "ping command not found.", "target": target}


def handle_client(conn: socket.socket, addr: tuple) -> None:
    print(f"[+] Connection from {addr[0]}:{addr[1]}")
    try:
        raw = conn.recv(1024).decode().strip()
        request = json.loads(raw)
        target = request.get("target", "")
        count = int(request.get("count", 4))

        if not target:
            response = {"success": False, "output": "No target specified.", "target": ""}
        else:
            print(f"    Pinging {target} ({count} packets) for {addr[0]}")
            response = run_ping(target, count)

        conn.sendall(json.dumps(response).encode())
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        error = json.dumps({"success": False, "output": f"Bad request: {e}", "target": ""})
        conn.sendall(error.encode())
    finally:
        conn.close()
        print(f"[-] Closed connection from {addr[0]}:{addr[1]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ping server")
    parser.add_argument("--host", default=HOST, help=f"Bind address (default: {HOST})")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port (default: {PORT})")
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((args.host, args.port))
        srv.listen(5)
        print(f"[*] Ping server listening on {args.host}:{args.port}")
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
