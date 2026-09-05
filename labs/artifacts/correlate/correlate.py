#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Correlate two timestamp series by timing alone (Lab 5.2).

Given two files of packet/event timestamps — one from the gateway uplink
(entry side) and one from a destination you own (exit side) — this bins both
into short time buckets and cross-correlates them over a range of lags. If the
two are the ends of one flow, their bursts line up (offset by the circuit's
delay) and the correlation is high. It reads nothing encrypted; timing is all
it uses. That is the whole point of the lab: correlation needs only both ends.

Pure standard library — no numpy — so it runs anywhere python3 does.
"""
import math
import random
import sys

BUCKET = 0.5      # seconds per bucket
MAX_LAG = 8       # buckets to slide while searching for the circuit delay
THRESHOLD = 0.70  # correlation at/above this = "same flow"


def load(path):
    ts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ts.append(float(line.split()[0]))
            except ValueError:
                pass
    return ts


def bucketize(ts, t0, n):
    v = [0] * n
    for t in ts:
        i = int((t - t0) / BUCKET)
        if 0 <= i < n:
            v[i] += 1
    return v


def pearson(a, b):
    n = len(a)
    if n == 0:
        return 0.0
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((x - mb) ** 2 for x in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def correlate(ts1, ts2):
    """Return (entry_active, exit_active, best_lag_buckets, best_corr)."""
    if not ts1 or not ts2:
        return (0, 0, 0, 0.0)
    t0 = min(min(ts1), min(ts2))
    t1 = max(max(ts1), max(ts2))
    n = int((t1 - t0) / BUCKET) + 1 + MAX_LAG
    A = bucketize(ts1, t0, n)
    B = bucketize(ts2, t0, n)
    best_lag, best = 0, -2.0
    for lag in range(-MAX_LAG, MAX_LAG + 1):
        a, b = [], []
        for i in range(len(A)):
            j = i + lag
            if 0 <= j < len(B):
                a.append(A[i])
                b.append(B[j])
        if len(a) < 4:
            continue
        c = pearson(a, b)
        if c > best:
            best, best_lag = c, lag
    return (sum(1 for x in A if x), sum(1 for x in B if x), best_lag, best)


def report(ts1, ts2):
    ea, eb, lag, corr = correlate(ts1, ts2)
    verdict = "SAME FLOW" if corr >= THRESHOLD else "weak match"
    print(f"entry buckets : {ea} active")
    print(f"exit  buckets : {eb} active")
    print(f"best lag      : {lag * BUCKET:+.1f} s")
    print(f"correlation   : {corr:.2f}   -> {verdict}")
    return corr


def _cluster(rng, centers, delay=0.0):
    """A burst is a cluster of packets, not a single event — that's what a real
    tcpdump of the uplink looks like. Spread ~8 packets across ~0.15 s."""
    out = []
    for c in centers:
        for _ in range(8):
            out.append(c + delay + rng.uniform(0.0, 0.15))
    return sorted(out)


def _synth_aligned(rng):
    centers = [i * 1.5 for i in range(10)]
    a = _cluster(rng, centers, delay=0.0)
    b = _cluster(rng, centers, delay=0.2)   # same bursts, one circuit-delay later
    return a, b


def _synth_unrelated(rng):
    ca = sorted(rng.uniform(0, 15) for _ in range(10))
    cb = sorted(rng.uniform(0, 15) for _ in range(10))
    return _cluster(rng, ca), _cluster(rng, cb)


def selftest():
    """Aligned series must read SAME FLOW; unrelated must not. Averaged over
    several seeds so the verdict doesn't hinge on one lucky draw."""
    al, un = [], []
    for seed in range(20):
        rng = random.Random(seed)
        al.append(correlate(*_synth_aligned(rng))[3])
        un.append(correlate(*_synth_unrelated(rng))[3])
    mean_al = sum(al) / len(al)
    mean_un = sum(un) / len(un)
    aligned_ok = all(c >= THRESHOLD for c in al)
    unrelated_ok = mean_un < THRESHOLD and mean_al - mean_un > 0.3
    ok = aligned_ok and unrelated_ok
    print(f"selftest: aligned mean={mean_al:.2f} (all >= {THRESHOLD}: {aligned_ok})")
    print(f"          unrelated mean={mean_un:.2f} (< {THRESHOLD}: {mean_un < THRESHOLD})")
    print(f"          separation={mean_al - mean_un:.2f}  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    if len(sys.argv) != 3:
        sys.stderr.write("usage: correlate.py <uplink.log> <dest.log>  |  --selftest\n")
        sys.exit(2)
    c = report(load(sys.argv[1]), load(sys.argv[2]))
    sys.exit(0 if c >= THRESHOLD else 1)
