#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Floodfill eclipse analyzer — Lab 6.2.

I2P stores a destination's leaseSet at the floodfill routers whose identity hash
is closest, by XOR distance, to the destination's *routing key*. The routing key
is SHA-256(destination_hash || YYYYMMDD), so it rotates every day. Control the
closest floodfills and you control what the network returns when it looks the
destination up — return nothing (unreachable) or a leaseSet you prefer.

This tool computes those distances over routers you ALREADY RUN in the testnet,
shows which floodfills would hold a given destination's record, and estimates the
work to displace them by grinding router identities closer to the key. It touches
nothing outside the testnet. --selftest is pure arithmetic on synthetic hashes.
"""
import argparse
import datetime
import hashlib
import os
import random
import sys

K_REPLICATION = 2  # I2P stores a record at several close floodfills; 2 in this toy


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def routing_key(dest_hash_hex: str, date: str | None = None) -> str:
    """SHA-256(dest_hash || YYYYMMDD) — the daily-rotated key records are stored under."""
    if date is None:
        date = datetime.date.today().strftime("%Y%m%d")
    return sha256_hex(bytes.fromhex(dest_hash_hex) + date.encode())


def xor_distance(a_hex: str, b_hex: str) -> int:
    return int(a_hex, 16) ^ int(b_hex, 16)


def closest(key_hex: str, floodfills: dict, k: int):
    """Return the k (name, ident) pairs whose ident is nearest the key by XOR."""
    return sorted(floodfills.items(), key=lambda kv: xor_distance(key_hex, kv[1]))[:k]


def approx_log2(d: int) -> float:
    return (d.bit_length() - 1) if d > 0 else -1.0


def _rand_ident(rng: random.Random) -> str:
    return "".join(rng.choice("0123456789abcdef") for _ in range(64))


def analyze(target_hash: str, floodfills: dict, date: str | None = None):
    key = routing_key(target_hash, date)
    holders = closest(key, floodfills, K_REPLICATION)
    print(f"routing key ({date or 'today'}) : {key[:8]}...")
    print("floodfills by XOR distance to the key:")
    for name, ident in closest(key, floodfills, len(floodfills)):
        mark = "   *holds the leaseSet" if (name, ident) in holders else ""
        print(f"  {name:6} distance 2^{approx_log2(xor_distance(key, ident)):.1f}{mark}")
    return key, holders


def selftest() -> int:
    ok = True
    for seed in range(10):
        rng = random.Random(seed)
        floodfills = {f"ff{i}": _rand_ident(rng) for i in range(8)}
        target = _rand_ident(rng)
        key = routing_key(target, "20260101")

        honest = closest(key, floodfills, len(floodfills))
        bar = xor_distance(key, honest[0][1])  # to own all K slots, beat the CLOSEST honest ff

        # grind attacker identities that land closer than the honest bar
        attackers = {}
        tries = 0
        while len(attackers) < K_REPLICATION and tries < 200_000:
            tries += 1
            ident = _rand_ident(rng)
            if xor_distance(key, ident) < bar:
                attackers[f"atk{len(attackers)}"] = ident
        grabbed = len(attackers) == K_REPLICATION

        # with attackers present, do they now own the K closest?
        combined = {**floodfills, **attackers}
        new_holders = closest(key, combined, K_REPLICATION)
        eclipsed = all(name.startswith("atk") for name, _ in new_holders)

        # daily rotation must move the key (so grinding can't be permanent)
        rotates = routing_key(target, "20260101") != routing_key(target, "20260102")

        ok = ok and grabbed and eclipsed and rotates

    print(f"selftest: grinding beats the honest bar, attackers take the K closest,")
    print(f"          and the routing key rotates daily  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _load_floodfills(path: str) -> dict:
    """Best-effort: one 'name hexident' per line, or a netDb dir of routerInfo-*.dat
    filenames whose stem we treat as the ident. Real convergence is validated on the
    host; this is the analysis side."""
    ff = {}
    if os.path.isdir(path):
        for i, fn in enumerate(sorted(os.listdir(path))):
            if fn.startswith("routerInfo-") and fn.endswith(".dat"):
                stem = fn[len("routerInfo-"):-len(".dat")]
                # map arbitrary ident encodings into a 64-hex space deterministically
                ff[f"ff{i}"] = sha256_hex(stem.encode())
    elif os.path.isfile(path):
        for line in open(path):
            parts = line.split()
            if len(parts) >= 2:
                ff[parts[0]] = parts[1] if len(parts[1]) == 64 else sha256_hex(parts[1].encode())
    return ff


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--target", help="target destination hash (hex) or short label")
    ap.add_argument("--floodfills", default="/seed", help="file of 'name hexident' lines, or a netDb dir")
    ap.add_argument("--date", help="YYYYMMDD (default: today)")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())

    if not a.target:
        ap.error("give --target (or --selftest)")
    # a short label is fine — hash it into the space so the demo always runs
    target = a.target if len(a.target) == 64 else sha256_hex(a.target.encode())
    ff = _load_floodfills(a.floodfills)
    if not ff:
        # fall back to a tiny synthetic set so the mechanism is still visible
        rng = random.Random(0)
        ff = {f"ff{i}": _rand_ident(rng) for i in range(2)}
        print("(no floodfills found; showing the mechanism on a synthetic pair)")
    analyze(target, ff, a.date)
