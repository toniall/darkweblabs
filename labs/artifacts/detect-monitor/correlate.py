#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Cross-surface correlation and dedup — Chapter 14 (Lab 14.5).

The same underlying event often shows on more than one surface: a victim listed on a leak
site and on its byte-identical mirror, a brand's pages moving in lockstep with its clone.
Emitting each as a separate alert is how a monitor drowns its analyst in duplicates. This
collapses them, echoing the Chapter 12 correlation but across the whole feed: using
Chapter 10 content identity, a mirror's copy of an event is folded into the canonical event on
the origin site, so a victim mirrored across two onions is ONE alert, not two. The event kept
is the one on the origin (a deadline slip on the real site, not a spurious "new victim" on the
mirror that was only new because the mirror itself was), and the number collapsed is reported —
because on a real feed that number is the difference between a readable alert stream and noise.
"""
import argparse
import os
import sys

import changefeed
import classify as classify_mod
import score as score_mod
import watchlist as wl_mod


def _mirror_map(timeline):
    m = {}
    for snap in timeline:
        for name, rec in snap["mirrors"].items():
            m[name] = rec.get("of")
    return m


def correlate(events, timeline):
    mirror_of = _mirror_map(timeline)

    def canon(surface):
        return mirror_of.get(surface, surface)

    groups = {}
    for e in events:
        groups.setdefault((e["name"], canon(e["surface"]), e["t_to"]), []).append(e)

    kept, collapsed = [], 0
    for (name, csurf, tt), grp in groups.items():
        if len(grp) == 1:
            kept.append(grp[0])
            continue
        # prefer the event already on the origin surface; else re-attribute the strongest
        origin = [e for e in grp if e["surface"] == csurf]
        winner = max(origin or grp, key=lambda e: e.get("rank", 0))
        if winner["surface"] != csurf:
            winner = winner | {"surface": csurf, "mirrored_from": winner["surface"]}
        winner = winner | {"seen_on": sorted({e["surface"] for e in grp})}
        kept.append(winner)
        collapsed += len(grp) - 1
    return {"events": kept, "collapsed": collapsed}


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    tl = changefeed.load_timeline(os.path.join(here, "corpus"))
    wl = wl_mod.build(os.path.join(here, "..", "persona-extract", "corpus"))
    scored = score_mod.score_all(classify_mod.classify_all(changefeed.feed(tl), wl), wl)
    res = correlate(scored, tl)
    ok = True

    if res["collapsed"] != 4:
        print(f"  collapsed dupes -> {res['collapsed']} (want 4: 3 mirror victims @t2 + 1 @t3)"); ok = False
    # the surviving Northwind@t2 event is the origin deadline_slip, not the mirror's new_victim
    nw = [e for e in res["events"] if e["name"] == "Northwind" and e["t_to"] == "t2"]
    if not (len(nw) == 1 and nw[0]["type"] == "deadline_slip" and nw[0]["surface"] == "RedLattice"):
        print(f"  Northwind@t2 after correlate -> {[(e['type'],e['surface']) for e in nw]}"); ok = False
    # no event should remain attributed to the mirror surface
    if any(e["surface"] == "RedLattice-m1" and e["type"] != "new_mirror" for e in res["events"]):
        print("  victim events should not remain on the mirror surface"); ok = False
    # the new_mirror event itself survives
    if not any(e["type"] == "new_mirror" for e in res["events"]):
        print("  new_mirror event should survive correlation"); ok = False

    print(f"selftest: {res['collapsed']} mirror-duplicated events collapse into their origin, the")
    print(f"          origin event is kept, and the new_mirror alert survives  -> {'PASS' if ok else 'FAIL'}")
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
        tl = changefeed.load_timeline(a.corpus)
        wl = wl_mod.build(os.path.join(here, "..", "persona-extract", "corpus"))
        scored = score_mod.score_all(classify_mod.classify_all(changefeed.feed(tl), wl), wl)
        res = correlate(scored, tl)
        if a.summary:
            print(f"    collapsed {res['collapsed']} cross-surface duplicates; {len(res['events'])} events remain")
        else:
            import json
            print(json.dumps(res, indent=2, default=str))
    else:
        ap.error("use --selftest or --corpus <dir>")
