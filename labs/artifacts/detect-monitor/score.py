#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Severity scoring — Chapter 14 (Lab 14.4).

Typing an event says what it is; scoring says how much it matters, which is what lets an
analyst read the few alerts that count instead of all of them. Every type carries a base
severity — an operator resurfacing or a clone impersonating is CRITICAL, a publication or a
new victim is HIGH, a withdrawal or a slid deadline or a market going dark is MEDIUM, a new
mirror is LOW, and cosmetic churn is SUPPRESS. The watchlist then supplies context and a
boost: a change to a WATCHED operator's own infrastructure is worth more than the same change
to an unknown one, so a watched market going dark is raised to HIGH. Confidence rides
alongside — hard-identifier events (a resurface keyed to a watched signature, a clone with a
swapped key) are high-confidence; the rest are medium — so the analyst reads both how bad and
how sure.
"""
import argparse
import os
import sys

import changefeed
import classify as classify_mod
import watchlist as wl_mod

RANK = {"suppress": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
_INV = {v: k for k, v in RANK.items()}

BASE = {
    "operator_resurface": "critical", "new_clone": "critical",
    "publication": "high", "new_victim": "high",
    "withdrawal": "medium", "deadline_slip": "medium", "market_down": "medium",
    "new_mirror": "low", "new_persona": "low", "content_change": "medium", "status_change": "low",
    "cosmetic_churn": "suppress",
}
HARD_CONF = {"operator_resurface", "new_clone"}


def _watched(ev, wl):
    op = (ev.get("after") or {}).get("operator") or (ev.get("before") or {}).get("operator")
    if ev["type"] == "operator_resurface":
        return True
    if op and wl_mod.watches(wl, handle=op):
        return True
    return False


def score(ev, wl):
    sev = BASE.get(ev["type"], "low")
    watched = _watched(ev, wl)
    # a watched operator's own infrastructure going dark is a lead indicator -> boost
    if watched and ev["type"] == "market_down":
        sev = _INV[min(4, RANK[sev] + 1)]
    conf = "high" if ev["type"] in HARD_CONF else "medium"
    return ev | {"severity": sev, "rank": RANK[sev], "watched": watched, "confidence": conf}


def score_all(events, wl):
    return [score(e, wl) for e in events]


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    tl = changefeed.load_timeline(os.path.join(here, "corpus"))
    wl = wl_mod.build(os.path.join(here, "..", "persona-extract", "corpus"))
    scored = score_all(classify_mod.classify_all(changefeed.feed(tl), wl), wl)
    ok = True

    def sev(name, tt):
        for e in scored:
            if e["name"] == name and e["t_to"] == tt:
                return e["severity"]
        return None

    checks = {
        ("n1ghthawk2", "t3"): "critical", ("NightHawkMkt-x", "t3"): "critical",
        ("Meridian", "t2"): "high", ("Coastal", "t2"): "high",
        ("Northwind", "t3"): "medium", ("RedLattice-m1", "t2"): "low",
    }
    for (n, tt), exp in checks.items():
        if sev(n, tt) != exp:
            print(f"  {n}@{tt} severity -> {sev(n,tt)} want {exp}"); ok = False
    # watched market going dark is boosted medium -> high
    md = next(e for e in scored if e["type"] == "market_down")
    if not (md["severity"] == "high" and md["watched"]):
        print(f"  watched market_down should boost to high -> {md['severity']}"); ok = False
    # churn suppressed
    if any(e["severity"] != "suppress" for e in scored if e["type"] == "cosmetic_churn"):
        print("  churn should be suppress"); ok = False
    # hard-confidence on the two criticals
    if not all(e["confidence"] == "high" for e in scored if e["type"] in HARD_CONF):
        print("  resurface/clone should be high confidence"); ok = False

    print(f"selftest: criticals score critical, a watched market going dark boosts to high,")
    print(f"          churn is suppress, and hard-identifier events are high confidence  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        here = os.path.dirname(os.path.abspath(__file__))
        wl = wl_mod.build(os.path.join(here, "..", "persona-extract", "corpus"))
        scored = score_all(classify_mod.classify_all(changefeed.feed(changefeed.load_timeline(a.corpus)), wl), wl)
        if a.summary:
            for e in sorted(scored, key=lambda x: -x["rank"]):
                w = " *watched*" if e["watched"] else ""
                print(f"    {e['severity']:8} {e['type']:20} {e['name']:16} @{e['surface']}{w}")
        else:
            import json
            print(json.dumps(scored, indent=2, default=str))
    else:
        ap.error("use --selftest or --corpus <dir>")
