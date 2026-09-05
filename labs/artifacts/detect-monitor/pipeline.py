#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""The detection pipeline — Chapter 14 (Labs 14.5-14.7).

Runs the whole watch loop over the timeline: diff snapshots into a raw feed, classify each
change, score it against the Chapter 13 watchlist, correlate away cross-surface duplicates,
then suppress the noise and rank what remains by severity — the short, ordered alert list an
analyst actually reads. The naive path is the monitor this chapter argues against: it alerts
on every raw diff, with no scoring, no dedup, and no suppression, so the real events are all
present but buried under churn and mirror duplicates. --selftest grades both against ground
truth with the detect scorer.
"""
import argparse
import json
import os
import sys

import changefeed
import classify as classify_mod
import correlate as correlate_mod
import score as score_mod
import watchlist as wl_mod

_KEEP = ("t_from", "t_to", "type", "name", "surface", "severity", "rank", "watched", "confidence")


def _clean(events):
    out = []
    for e in events:
        a = {k: e[k] for k in _KEEP if k in e}
        if e.get("seen_on") and len(e["seen_on"]) > 1:
            a["seen_on"] = e["seen_on"]
        out.append(a)
    return out


def _persona_corpus():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "persona-extract", "corpus")


def run(corpus_dir, persona_corpus=None, naive=False):
    tl = changefeed.load_timeline(corpus_dir)
    wl = wl_mod.build(persona_corpus or _persona_corpus())
    typed = classify_mod.classify_all(changefeed.feed(tl), wl)
    if naive:
        alerts = [e | {"severity": "unranked", "rank": -1} for e in typed]
        return {"alerts": _clean(alerts), "suppressed": 0, "collapsed": 0}
    scored = score_mod.score_all(typed, wl)
    res = correlate_mod.correlate(scored, tl)
    suppressed = sum(1 for e in res["events"] if e["severity"] == "suppress")
    kept = [e for e in res["events"] if e["severity"] != "suppress"]
    kept.sort(key=lambda e: (-e["rank"], e["t_to"], e["name"]))
    return {"alerts": _clean(kept), "suppressed": suppressed, "collapsed": res["collapsed"]}


def _summary(out, naive):
    mode = "naive monitor" if naive else "full monitor"
    print(f"    {mode}: {len(out['alerts'])} alerts  (suppressed {out['suppressed']} churn, collapsed {out['collapsed']} duplicates)")
    for a in out["alerts"]:
        sev = a["severity"].upper() if a["severity"] in ("critical", "high") else a["severity"]
        w = " *watched*" if a.get("watched") else ""
        print(f"    {sev:9} {a['type']:20} {a['name']:16} @{a['surface']}{w}")


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    corpus = os.path.join(here, "corpus")
    sys.path.insert(0, os.path.join(here, "..", "detect-scorer"))
    import scorer
    truth = json.load(open(os.path.join(here, "..", "detect-scorer", "manifest.json")))
    full = scorer.score(truth, run(corpus))
    naive = scorer.score(truth, run(corpus, naive=True))

    ok = True
    if not (full["alert_recall"] == 1.0 and full["alert_precision"] == 1.0 and full["false_alerts"] == 0
            and full["critical_ok"] == full["critical_total"]):
        print(f"  full -> {full}"); ok = False
    if not (naive["false_alerts"] > 0 and naive["alert_precision"] < full["alert_precision"]
            and naive["critical_ok"] < naive["critical_total"]):
        print(f"  naive -> {naive}"); ok = False

    print(f"selftest: full precision {full['alert_precision']:.2f}/false-alerts {full['false_alerts']}/"
          f"criticals {full['critical_ok']}/{full['critical_total']}; naive precision "
          f"{naive['alert_precision']:.2f}/false-alerts {naive['false_alerts']}  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--persona-corpus")
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        out = run(a.corpus, a.persona_corpus, naive=a.naive)
        if a.summary:
            _summary(out, a.naive)
            sys.exit(0)
        text = json.dumps(out, indent=2)
        if a.out:
            open(a.out, "w").write(text)
            print(f"wrote {a.out} ({'naive' if a.naive else 'full'} monitor)")
        else:
            print(text)
    else:
        ap.error("use --selftest or --corpus <dir> [--naive] [--summary] [--out file]")
