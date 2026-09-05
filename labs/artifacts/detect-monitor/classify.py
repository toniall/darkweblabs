#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Event classification — Chapter 14 (Lab 14.3).

A raw diff is not yet intelligence; its type is. This assigns every raw change a label from a
dark-web taxonomy so that later stages can score and route it. A victim that appeared is a
new_victim; one that turned published is a publication; one that vanished without publishing
is a withdrawal (paid or pulled); a deadline that moved later is a deadline_slip (countdown
theatre). A market going dark is market_down. A newly seen mirror is a new_mirror; a look-alike
of a known site carrying a swapped key is a new_clone (impersonation). A page whose banner
flipped while its content identity held is cosmetic_churn — the noise this chapter learns to
suppress. And the type that ties detection back to attribution: a newly seen persona whose
signed key is on the Chapter 13 watchlist is an operator_resurface — a watched operator back
under a new mask.
"""
import argparse
import os
import sys

import changefeed
import watchlist as wl_mod


def classify(ev, wl):
    k = ev["klass"]
    if k == "victim":
        bef, aft = ev["before"], ev["after"]
        if aft is None:
            return "withdrawal" if (bef or {}).get("status") != "published" else "victim_removed"
        if bef is None:
            return "new_victim"
        if aft.get("status") == "published" and bef.get("status") != "published":
            return "publication"
        db, da = bef.get("deadline", "-"), aft.get("deadline", "-")
        if db != "-" and da != "-" and da > db:
            return "deadline_slip"
        return "status_change"
    if k == "site":
        return "market_down" if ev["after"].get("state") == "down" else "site_restored"
    if k == "mirror":
        return "new_mirror"
    if k == "clone":
        return "new_clone"
    if k == "persona":
        sk = ev["after"].get("signed_key", "-")
        w = ev["after"].get("wallet", "-")
        if wl_mod.watches(wl, key=sk, wallet=w):
            return "operator_resurface"
        return "new_persona"
    if k == "page":
        bef, aft = ev["before"], ev["after"]
        if bef.get("content_id") == aft.get("content_id"):
            return "cosmetic_churn"
        return "content_change"
    return "unknown"


def classify_all(events, wl):
    return [ev | {"type": classify(ev, wl)} for ev in events]


def _resurface_operator(ev, wl):
    sk = ev["after"].get("signed_key", "-") if ev.get("after") else "-"
    for op in wl["operators"]:
        if sk in op["keys"]:
            return op["operator"], op["members"]
    return None, None


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    tl = changefeed.load_timeline(os.path.join(here, "corpus"))
    wl = wl_mod.build(os.path.join(here, "..", "persona-extract", "corpus"))
    typed = classify_all(changefeed.feed(tl), wl)
    ok = True

    def typ(name, tt, surface=None):
        for e in typed:
            if e["name"] == name and e["t_to"] == tt and (surface is None or e["surface"] == surface):
                return e["type"]
        return None

    want = {
        ("Coastal", "t2", "RedLattice"): "new_victim",
        ("Meridian", "t2", "RedLattice"): "publication",
        ("Northwind", "t2", "RedLattice"): "deadline_slip",
        ("Northwind", "t3", "RedLattice"): "withdrawal",
        ("NightHawkMkt", "t2", None): "market_down",
        ("RedLattice-m1", "t2", None): "new_mirror",
        ("NightHawkMkt-x", "t3", None): "new_clone",
        ("n1ghthawk2", "t3", None): "operator_resurface",
    }
    for (name, tt, surf), exp in want.items():
        got = typ(name, tt, surf)
        if got != exp:
            print(f"  {name}@{tt}: got {got}, want {exp}"); ok = False
    churn = sum(1 for e in typed if e["type"] == "cosmetic_churn")
    if churn != 10:
        print(f"  cosmetic churn count -> {churn} (want 10)"); ok = False
    op, _ = _resurface_operator(next(e for e in typed if e["type"] == "operator_resurface"), wl)
    if op is None:
        print("  resurface should name a watched operator"); ok = False

    print(f"selftest: every landmark change types correctly and the {churn} banner flips are")
    print(f"          cosmetic_churn; the resurfacing persona maps to a watched operator  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--persona-corpus")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        wl = wl_mod.build(a.persona_corpus or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "persona-extract", "corpus"))
        typed = classify_all(changefeed.feed(changefeed.load_timeline(a.corpus)), wl)
        if a.summary:
            from collections import Counter
            print(f"    typed events: {len(typed)}")
            for e in typed:
                print(f"    {e['t_from']}->{e['t_to']}  {e['type']:20} {e['name']:16} @{e['surface']}")
            print("    ---")
            for t, n in sorted(Counter(e["type"] for e in typed).items(), key=lambda kv: -kv[1]):
                print(f"    {n:3}  {t}")
        else:
            import json
            print(json.dumps(typed, indent=2, default=str))
    else:
        ap.error("use --selftest or --corpus <dir>")
