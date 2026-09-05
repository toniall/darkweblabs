#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Crawler frontier + scope guard — Chapter 9 (Labs 9.1, 9.2, 9.3).

The brain of the crawler, with no network in it: URL normalization, per-address
network classification (tor / i2p / hyphanet / clearnet), a seen-set, a seed-driven
frontier, a politeness scheduler, and the scope guard that keeps collection pointed
at the range and nowhere else. Pure logic, so it self-tests offline; the actual
fetch-through-Tor lives in crawl.py and is injected.

Scope guard (the safety control): the crawler fetches an address only if its network
is a dark-web network (never clearnet) AND its host is on the allowlist built from
the range's own published services. Everything else is refused. This is the Chapter 9
analogue of Chapter 5's toothless attacks and Chapter 8's watermarked content.
"""
import argparse
import re
import sys
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

DARK_NETWORKS = ("tor", "i2p", "hyphanet")
_ONION_RE = re.compile(r"[a-z2-7]{56}\.onion", re.I)
_HYPHANET_RE = re.compile(r"\b(USK|SSK|CHK|KSK)@", re.I)


def classify_network(addr):
    """Return the network an address belongs to, from its form alone."""
    if not addr:
        return "unknown"
    if _HYPHANET_RE.search(addr):
        return "hyphanet"
    host = urlsplit(addr).hostname or addr
    if host.endswith(".b32.i2p") or host.endswith(".i2p"):
        return "i2p"
    if _ONION_RE.search(host) or host.endswith(".onion"):
        return "tor"
    if addr.startswith(("http://", "https://")) or "." in host:
        return "clearnet"
    return "unknown"


def host_of(addr):
    """The comparable host/key for an address (onion, eepsite, or Hyphanet key)."""
    m = _HYPHANET_RE.search(addr or "")
    if m:
        # a Hyphanet key identity: up to the site name, ignore the version/edition
        key = addr[m.start():]
        return key.split("/")[0]
    return (urlsplit(addr).hostname or addr).lower()


def normalize_url(url, base=None):
    """Resolve against base, lowercase host, drop fragment + default port,
    and canonicalise the path so the seen-set doesn't double-count."""
    if base:
        url = urljoin(base, url)
    parts = urlsplit(url)
    scheme = parts.scheme or "http"
    host = (parts.hostname or "").lower()
    if parts.port and not ((scheme == "http" and parts.port == 80) or
                           (scheme == "https" and parts.port == 443)):
        host = f"{host}:{parts.port}"
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return urlunsplit((scheme, host, path, parts.query, ""))


class Frontier:
    """Seed-driven work queue with a seen-set, scope guard, and politeness."""

    def __init__(self, allow=None, min_delay=1.0):
        self.allow = set(allow or [])          # hosts/keys the range published
        self.min_delay = float(min_delay)
        self.seen = set()
        self.queue = []
        self._last = {}                        # host -> last fetch time (politeness)

    def in_scope(self, addr):
        net = classify_network(addr)
        if net not in DARK_NETWORKS:           # never clearnet / unknown
            return False
        return host_of(addr) in self.allow     # only range-published hosts

    def seed(self, addrs):
        for a in addrs:
            self.allow.add(host_of(a))          # a seed is trusted, and in scope
        for a in addrs:
            self.add(a)

    def add(self, url, base=None):
        norm = normalize_url(url, base)
        if not self.in_scope(norm):
            return False
        if norm in self.seen:
            return False
        self.seen.add(norm)
        self.queue.append(norm)
        return True

    def wait_for(self, addr):
        """Seconds a polite crawler should sleep before fetching this host."""
        host = host_of(addr)
        last = self._last.get(host)
        if last is None:
            return 0.0
        return max(0.0, self.min_delay - (time.monotonic() - last))

    def mark_fetched(self, addr):
        self._last[host_of(addr)] = time.monotonic()

    def next(self):
        return self.queue.pop(0) if self.queue else None

    def __len__(self):
        return len(self.queue)


def selftest():
    ok = True

    # classification
    onion = "http://" + "a" * 56 + ".onion"
    cases = {
        onion: "tor",
        "http://identifier.b32.i2p/": "i2p",
        "USK@abc123/site/0/": "hyphanet",
        "https://example.com/path": "clearnet",
    }
    for addr, want in cases.items():
        if classify_network(addr) != want:
            print(f"  classify {addr!r} -> {classify_network(addr)} != {want}")
            ok = False

    # normalization: relative resolve, fragment + default port drop, trailing slash
    if normalize_url("/b/", base=onion + "/a") != onion + "/b":
        ok = False
    if normalize_url(onion + ":80/x#frag") != onion + "/x":
        ok = False
    if normalize_url(onion + "/") != normalize_url(onion):   # root canonicalises stably
        ok = False

    # scope guard: clearnet refused, off-allow onion refused, seeded onion allowed
    f = Frontier()
    f.seed([onion])
    other = "http://" + "b" * 56 + ".onion"
    if f.in_scope("https://example.com"):            # clearnet must be refused
        ok = False
    if f.in_scope(other):                            # unknown onion must be refused
        ok = False
    if not f.in_scope(onion + "/listings"):          # same-host range path allowed
        ok = False

    # frontier: dedup + only-in-scope enqueue
    f2 = Frontier()
    f2.seed([onion])                                 # queues the seed once
    added = f2.add(onion + "/a")                      # new in-scope path -> queued
    dup = f2.add(onion + "/a/")                       # normalises to same -> refused
    off = f2.add(other)                              # off-allow -> refused
    if not (added and not dup and not off and len(f2) == 2):
        print(f"  frontier add/dedup/scope wrong (len={len(f2)})")
        ok = False

    # politeness: first fetch immediate, second must wait
    f3 = Frontier(min_delay=5.0)
    f3.seed([onion])
    if f3.wait_for(onion) != 0.0:
        ok = False
    f3.mark_fetched(onion)
    if not (0.0 < f3.wait_for(onion) <= 5.0):
        ok = False

    print("selftest: classification, normalization, the scope guard (clearnet and")
    print(f"          off-range refused), dedup, and politeness all hold  -> "
          f"{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--classify", metavar="ADDR", help="print the network of one address")
    a = ap.parse_args()
    if a.classify:
        print(classify_network(a.classify))
    elif a.selftest:
        sys.exit(selftest())
    else:
        ap.error("use --selftest or --classify ADDR")
