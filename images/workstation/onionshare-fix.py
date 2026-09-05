#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Make OnionShare work in the split lab: reachable hosting, and a chat socket
that actually pumps frames.

1. onion.py — point the ephemeral onion's target at the workstation's internal
   address instead of tor's (the gateway's) loopback, so the gateway can reach
   the server. Pairs with the Whonix bind marker created in the Dockerfile.

2. web.py — move chat off gevent. OnionShare asks for async_mode="gevent", but
   gevent-websocket is unmaintained and stalls on Python 3.12: the chat
   WebSocket upgrades to 101 and then never delivers a frame. Repoint chat at
   flask-socketio's maintained threading + simple-websocket path (installed in
   the Dockerfile), which works on 3.12. threading also needs the Werkzeug
   server's allow_unsafe_werkzeug flag to start.

Idempotent and non-fatal: each patch reports what it did, and a version whose
source differs only warns, so the image still builds.
"""
import os
import re
import sys

ws_ip = sys.argv[1] if len(sys.argv) > 1 else "10.152.152.11"

import onionshare_cli

pkg = os.path.dirname(onionshare_cli.__file__)


def backup_once(path, original):
    if not os.path.exists(path + ".orig"):
        open(path + ".orig", "w", encoding="utf-8").write(original)


# ── 1. onion target -> the workstation ───────────────────────────────────────
onion_py = os.path.join(pkg, "onion.py")
if os.path.isfile(onion_py):
    src = open(onion_py, encoding="utf-8").read()
    if ws_ip in src:
        print(f"[onionshare-fix] onion.py: already targets {ws_ip}")
    else:
        new, n = re.subn(r"\{80:\s*port\}", '{80: "%s:%%d" %% port}' % ws_ip, src)
        if n:
            backup_once(onion_py, src)
            open(onion_py, "w", encoding="utf-8").write(new)
            print(f"[onionshare-fix] onion.py: onion target -> {ws_ip}:port ({n} site(s))")
        else:
            sys.stderr.write("[onionshare-fix] WARNING onion.py: {80: port} not "
                             "found; hosting may stay broken on this version\n")
else:
    sys.stderr.write("[onionshare-fix] WARNING: onion.py not found\n")

# ── 2. chat -> threading + simple-websocket ──────────────────────────────────
web_py = os.path.join(pkg, "web", "web.py")
if os.path.isfile(web_py):
    w = open(web_py, encoding="utf-8").read()
    worig = w
    w = w.replace('async_mode="gevent"', 'async_mode="threading"')
    w = w.replace('async_mode="eventlet"', 'async_mode="threading"')
    w = w.replace(
        "self.socketio.run(self.app, host=host, port=port)",
        "self.socketio.run(self.app, host=host, port=port, allow_unsafe_werkzeug=True)",
    )
    if w != worig:
        backup_once(web_py, worig)
        open(web_py, "w", encoding="utf-8").write(w)
        print("[onionshare-fix] web.py: chat -> threading + simple-websocket")
    else:
        print("[onionshare-fix] web.py: chat already patched or pattern differs")
else:
    sys.stderr.write("[onionshare-fix] WARNING: web.py not found\n")

print("[onionshare-fix] done")
