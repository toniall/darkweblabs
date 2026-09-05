#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Small-world key routing + content-hash keys — Lab 7.4 / 7.2.

Hyphanet has no host to reach. A request for a key is routed greedily through the
node graph toward the node whose *location* (a point on a circular keyspace) is
closest to the key's location; on a small-world graph, short paths exist between
far-apart locations. Separately, a CHK addresses content by the hash of that
content, so the key that finds a block also verifies it.

This tool models both over a synthetic node graph — it reasons about routing and
key derivation, and touches nothing outside itself. --selftest is pure arithmetic.
"""
import argparse
import hashlib
import random
import sys


# ---- content-hash keys (CHK) -------------------------------------------------

def chk(content: bytes) -> str:
    """A CHK-like key derived from the content: the routing part is a hash of the
    data, so fetching + re-hashing verifies integrity."""
    h = hashlib.sha256(content).hexdigest()
    return f"CHK@{h[:16]}...,{h[16:32]}...,AAMC8mI"


def chk_verify(content: bytes, key: str) -> bool:
    return chk(content) == key


# ---- circular keyspace + greedy routing --------------------------------------

def location(label: str) -> float:
    """Map any id/key label to a point in [0,1) — its place on the ring."""
    d = hashlib.sha256(label.encode()).digest()
    return int.from_bytes(d[:8], "big") / 2**64


def cdist(a: float, b: float) -> float:
    d = abs(a - b)
    return min(d, 1.0 - d)


def greedy_route(start, target_loc, loc, adj, max_hops):
    """Move to the neighbour closest to target_loc while that is strictly closer
    than the current node; return the path taken."""
    cur = start
    path = [cur]
    for _ in range(max_hops):
        here = cdist(loc[cur], target_loc)
        best = min(adj[cur], key=lambda n: cdist(loc[n], target_loc), default=cur)
        if best != cur and cdist(loc[best], target_loc) < here:
            cur = best
            path.append(cur)
        else:
            break
    return path


def _build_smallworld(rng, n, long_links=2):
    """A ring (each node linked to its two ring-neighbours) plus a few random
    long-range links per node — a small-world graph. The ring guarantees greedy
    routing always makes progress to the globally-closest node; the long links
    make the paths short."""
    ids = [f"n{i}" for i in range(n)]
    loc = {node: i / n for i, node in enumerate(ids)}  # evenly spaced on the ring
    adj = {node: set() for node in ids}
    for i, node in enumerate(ids):
        adj[node].add(ids[(i - 1) % n])
        adj[node].add(ids[(i + 1) % n])
    for node in ids:
        for _ in range(long_links):
            other = rng.choice(ids)
            if other != node:
                adj[node].add(other)
                adj[other].add(node)
    return ids, loc, {k: sorted(v) for k, v in adj.items()}


def selftest() -> int:
    ok = True
    for seed in range(10):
        rng = random.Random(seed)
        ids, loc, adj = _build_smallworld(rng, n=40, long_links=2)
        closest_of = lambda t: min(ids, key=lambda node: cdist(loc[node], t))

        hops = []
        for _ in range(25):
            key = _rand_key(rng)
            t = location(key)
            start = rng.choice(ids)
            path = greedy_route(start, t, loc, adj, max_hops=len(ids))
            # ring guarantees greedy reaches the globally-closest node
            if path[-1] != closest_of(t):
                ok = False
            hops.append(len(path) - 1)

        # small-world: average path is well under a half-ring walk
        if sum(hops) / len(hops) >= len(ids) / 2:
            ok = False

        # CHK: address == hash of content, and tampering is detected
        blob = bytes(rng.randrange(256) for _ in range(64))
        k = chk(blob)
        if not chk_verify(blob, k) or chk_verify(blob + b"x", k):
            ok = False

    print("selftest: greedy key-routing converges on the closest node via short")
    print("          small-world paths, and CHK addressing detects tampering"
          f"  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _rand_key(rng):
    return "".join(rng.choice("0123456789abcdef") for _ in range(32))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--route", metavar="KEY", help="route a demo request toward KEY's location")
    ap.add_argument("--nodes", type=int, default=40)
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())

    rng = random.Random(0)
    ids, loc, adj = _build_smallworld(rng, a.nodes)
    key = a.route or _rand_key(rng)
    t = location(key)
    start = rng.choice(ids)
    path = greedy_route(start, t, loc, adj, max_hops=len(ids))
    closest = min(ids, key=lambda node: cdist(loc[node], t))
    print(f"key            : {key}")
    print(f"key location   : {t:.4f} on the ring")
    print(f"route          : {' -> '.join(path)}")
    print(f"reached        : {path[-1]} (closest node is {closest}) in {len(path)-1} hops")
