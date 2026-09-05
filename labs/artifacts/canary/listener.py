#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Lab 5.5 beacon listener — the 'attacker's' callback receiver, defanged.

Logs every hit (source address + time). It only ever receives the lab canary's
beacon, which is aimed at a lab-internal address. There is no exploit here and
nothing that executes; it is a web server that records that a request arrived.
"""
import datetime
import http.server
import os

PORT = int(os.environ.get("CANARY_PORT", "8971"))
# a 1x1 transparent GIF — the "tracking pixel" the canary document requests
PIXEL = bytes.fromhex(
    "47494638396101000100800000000000ffffff21f90401000000002c"
    "00000000010001000002024401003b"
)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        src = self.client_address[0]
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] BEACON from {src}  path={self.path}", flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "image/gif")
        self.send_header("Content-Length", str(len(PIXEL)))
        self.end_headers()
        self.wfile.write(PIXEL)

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"listener on 0.0.0.0:{PORT}", flush=True)
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
