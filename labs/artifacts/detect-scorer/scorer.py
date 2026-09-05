#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Detection scoring harness — Chapter 14 (Lab 14.7).

Grades a monitor's alert stream against the detect-lab ground truth. It reports alert recall
(did the real events surface), alert precision (of everything put in front of the analyst, the
fraction that were distinct real alerts), and — the metric that matters most here — the
false-alert count, because in monitoring the dangerous failure is crying wolf: a stream full
of noise trains an analyst to ignore it, and the buried critical is the one that gets missed.
It also checks whether the two CRITICAL events surfaced AT critical severity (prioritisation),
and reports how much churn was suppressed and how many duplicates collapsed. Pure Python;
ships its answer key and a sample, and self-tests.
"""
import argparse
import json
import os
import sys


def _key(a):
    return (a["name"], a.get("t") or a.get("t_to"), a["type"])


def _ratio(n, d):
    return round(n / d, 2) if d else 1.0


def score(truth, output):
    true_sev = {_key(a): a["severity"] for a in truth["alerts"]}
    alerts = output.get("alerts", [])

    matched = {k for k in (_key(a) for a in alerts) if k in true_sev}
    false = [a for a in alerts if _key(a) not in true_sev]

    crit = truth.get("critical", [])
    crit_ok = 0
    for name, t in crit:
        if any(a["name"] == name and (a.get("t") or a.get("t_to")) == t
               and a.get("severity") == "critical" for a in alerts):
            crit_ok += 1

    return {
        "alert_recall": _ratio(len(matched), len(true_sev)), "recall_ok": len(matched), "recall_total": len(true_sev),
        "alert_precision": _ratio(len(matched), len(alerts)), "alerts_emitted": len(alerts),
        "false_alerts": len(false),
        "critical_ok": crit_ok, "critical_total": len(crit),
        "suppressed": output.get("suppressed", 0), "collapsed": output.get("collapsed", 0),
    }


def render(r):
    return "\n".join([
        "scored the alert stream against detect-lab ground truth",
        f"  alert recall           {r['recall_ok']} / {r['recall_total']}      {r['alert_recall']:.2f}",
        f"  alert precision        {r['recall_ok']} / {r['alerts_emitted']}     {r['alert_precision']:.2f}",
        f"  false alerts           {r['false_alerts']}          (noise shown to the analyst — the crying-wolf count)",
        f"  criticals surfaced     {r['critical_ok']} / {r['critical_total']}      (at critical severity, ranked to the top)",
        f"  churn suppressed       {r['suppressed']}",
        f"  duplicates collapsed   {r['collapsed']}",
    ])


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    truth = json.load(open(os.path.join(here, "manifest.json")))
    sample = json.load(open(os.path.join(here, "sample-alerts.json")))
    r = score(truth, sample)
    ok = (r["alert_recall"] == 1.0 and r["alert_precision"] == 1.0 and r["false_alerts"] == 0
          and r["critical_ok"] == r["critical_total"])
    print(render(r))
    print(f"selftest: grades the sample alert stream  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.file:
        here = os.path.dirname(os.path.abspath(__file__))
        truth = json.load(open(os.path.join(here, "manifest.json")))
        print(render(score(truth, json.load(open(a.file)))))
    else:
        ap.error("pass an alerts.json or --selftest")
