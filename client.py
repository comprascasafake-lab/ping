#!/usr/bin/env python3
"""Ping client: sends ping requests to a ping server and displays results."""

import socket
import json
import argparse
import sys

DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 9999


def request_ping(server_host: str, server_port: int, target: str, count: int) -> dict:
    request = json.dumps({"target": target, "count": count})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(35)
        s.connect((server_host, server_port))
        s.sendall(request.encode())

        chunks = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)

    return json.loads(b"".join(chunks).decode())


def main() -> None:
    parser = argparse.ArgumentParser(description="Ping client")
    parser.add_argument("target", help="Host or IP to ping")
    parser.add_argument(
        "--server", default=DEFAULT_SERVER_HOST, help=f"Server address (default: {DEFAULT_SERVER_HOST})"
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_SERVER_PORT, help=f"Server port (default: {DEFAULT_SERVER_PORT})"
    )
    parser.add_argument(
        "--count", type=int, default=4, help="Number of ping packets (default: 4)"
    )
    args = parser.parse_args()

    print(f"[*] Connecting to ping server at {args.server}:{args.port}")
    print(f"[*] Requesting ping to: {args.target} ({args.count} packets)\n")

    try:
        response = request_ping(args.server, args.port, args.target, args.count)
    except ConnectionRefusedError:
        print(f"[!] Could not connect to server {args.server}:{args.port}", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print("[!] Connection timed out.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("[!] Invalid response from server.", file=sys.stderr)
        sys.exit(1)

    status = "OK" if response.get("success") else "FAIL"
    print(f"[{status}] Result for {response.get('target', args.target)}:")
    print("-" * 50)
    print(response.get("output", "").strip())


if __name__ == "__main__":
    main()
