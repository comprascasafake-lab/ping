#!/usr/bin/env python3
"""Simple HTTP server that accepts file uploads via multipart POST."""

import argparse
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

UPLOAD_DIR = "/tmp/ping-remote/uploads"


class UploadHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Expected multipart/form-data")
            return

        boundary = content_type.split("boundary=")[-1].encode()
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        saved = []
        for part in body.split(b"--" + boundary):
            if b"Content-Disposition" not in part:
                continue
            header, _, content = part.partition(b"\r\n\r\n")
            content = content.rstrip(b"\r\n--")
            if b'filename="' in header:
                filename = header.split(b'filename="')[1].split(b'"')[0].decode()
                dest = os.path.join(UPLOAD_DIR, filename)
                with open(dest, "wb") as f:
                    f.write(content)
                saved.append(dest)
                print(f"[+] Saved: {dest}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(("\n".join(saved) or "no files").encode())

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="Upload server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), UploadHandler)
    print(f"[*] Upload server listening on {args.host}:{args.port}")
    print(f"[*] Files saved to {UPLOAD_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
