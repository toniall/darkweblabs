#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Live crawl driver — runs the Chapter 9 crawler against the range through Tor.

This is the fetch layer the selftest fixture stands in for: it drives crawl.crawl()
with a real fetch that reaches the range's onion services over the workstation's Tor
SOCKS proxy (via curl, so there is no Python SOCKS dependency). It reads the range's
published services as the scope allowlist, seeds from the directory, and writes a
crawl-output.json the Chapter 8 scorer grades.

Runs inside the workstation container, where Tor egress and the range are reachable
(./lab crawl range). It cannot run in the static sandbox — the crawler's brain
(frontier, extract, crawl) is what self-tests offline; this wires it to real Tor.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from crawl import crawl
from frontier import host_of


def make_fetch(socks, jar, delay):
    """A fetch(addr, session)->(status, html, headers) backed by curl over SOCKS.
    A cookie jar carries the session so the login wall can be walked once."""
    def fetch(addr, session):
        use_jar = session is not None
        cmd = ["curl", "-sS", "-m", "40", "--socks5-hostname", socks,
               "-o", "-", "-D", "-"]
        if use_jar:
            cmd += ["-c", jar, "-b", jar]
        cmd.append(addr)
        try:
            out = subprocess.run(cmd, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            return 0, "", {}                    # a slow/absent onion — normal case
        raw = out.stdout.decode("utf-8", "replace")
        head, _, body = raw.partition("\r\n\r\n")
        status = 0
        headers = {}
        for i, line in enumerate(head.splitlines()):
            if i == 0 and line.startswith("HTTP/"):
                parts = line.split()
                status = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            elif ":" in line:
                k, _, v = line.partition(":")
                headers[k.strip().lower()] = v.strip()
        return status, body, headers
    return fetch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="where to write crawl-output.json")
    ap.add_argument("--naive", action="store_true",
                    help="a first crawl with sessions, dedup, and clone detection off")
    ap.add_argument("--socks", default=os.environ.get("LAB_SOCKS", "socks5h://gateway:9050"))
    ap.add_argument("--delay", type=float, default=float(os.environ.get("LAB_DELAY", "2.0")))
    a = ap.parse_args()

    # scope + seed come from the range itself: LAB_ALLOW is every published host,
    # LAB_SEED is the directory. ./lab crawl fills these from ./lab range list.
    allow = [h for h in os.environ.get("LAB_ALLOW", "").split(",") if h]
    seed = os.environ.get("LAB_SEED", "")
    if not allow or not seed:
        sys.exit("LAB_ALLOW and LAB_SEED must be set (run via ./lab crawl range)")
    allow = [host_of(h) for h in allow]

    jar = os.path.join(tempfile.gettempdir(), "crawl-cookies.txt")
    fetch = make_fetch(a.socks.replace("socks5h://", ""), jar, a.delay)
    full = not a.naive
    output = crawl([seed], fetch, allow, min_delay=a.delay,
                   sessions=full, dedup=full, detect_clones=full)
    with open(a.out, "w") as fh:
        json.dump(output, fh, indent=2)
    print(f"wrote {a.out}: {len(output['discovered'])} services "
          f"({'full engine' if full else 'naive crawl'})")


if __name__ == "__main__":
    main()
