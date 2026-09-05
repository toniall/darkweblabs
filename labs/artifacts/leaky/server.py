#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Deliberately-leaky web service for Lab 4.6.

Published over Tor as an onion, it nonetheless gives its real location away the
way careless real services do — in response headers and an enabled status page.
The lesson: Tor hid the network path; the *application* undid it by introducing
itself. Nothing here is exotic; every leak below is one seen in the wild.
"""
import http.server
import os
import socket

def real_ip():
    """The address this host actually uses to reach the network — the thing Tor
    was hiding, and the thing a careless app hands right back."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((os.environ.get("LAB_GATEWAY_IP", "10.152.152.10"), 9051))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

IP = real_ip()
HOSTNAME = socket.gethostname()
PORT = int(os.environ.get("LEAKY_PORT", "8899"))
_seen = {"n": 0}

class Leaky(http.server.BaseHTTPRequestHandler):
    server_version = "Werkzeug/3.0"   # looks like a Flask dev server left exposed
    sys_version = "Python/3.12"

    def _body_for(self, path):
        if path.rstrip("/") == "/server-status":
            return (
                "Server Status\n"
                f"Local address : {IP}:{PORT}\n"
                f"Hostname      : {HOSTNAME}\n"
                f"Uplink        : eth0 {IP}/24\n"
                f"Requests      : {_seen['n']}\n"
            ).encode()
        return (
            "<html><body><h1>Leaky Corp</h1>"
            "<p>hello from an onion</p></body></html>\n"
        ).encode()

    def _send_headers(self, body):
        self.send_response(200)
        # the leaks: a backend name + address, and a proxy Via line nobody meant to add
        self.send_header("X-Served-By", f"backend-01 ({IP})")
        self.send_header("Via", f"1.1 ip-{IP.replace('.', '-')}.internal")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

    def do_HEAD(self):
        self._send_headers(self._body_for(self.path))

    def do_GET(self):
        _seen["n"] += 1
        body = self._body_for(self.path)
        self._send_headers(body)
        self.wfile.write(body)

    def log_message(self, *a):
        pass  # quiet

if __name__ == "__main__":
    print(f"serving on {IP}:{PORT}", flush=True)
    http.server.HTTPServer(("0.0.0.0", PORT), Leaky).serve_forever()
