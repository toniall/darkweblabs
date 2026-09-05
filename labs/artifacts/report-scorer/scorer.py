#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Report scoring harness — Chapter 15 (Lab 15.7).

Grades an intelligence report against the ground-truth claim set. It reports claim coverage (did
the report make the findings), provenance completeness (does every claim trace to a source), and
calibration (do the stated type and confidence match what the evidence supports) — and, the metric
that matters most here, the OVERCLAIM count: the number of claims presented more strongly than the
evidence licenses. Overclaiming is the reporting analog of the whole book's dangerous errors — the
false merge, the bluff, the false alert — turned inward on the analyst's own integrity: a report
that launders assessments into facts and hides its sourcing is one a decision-maker cannot audit,
and cannot safely act on. Pure Python; ships its answer key and a sample, and self-tests.
"""
import argparse
import json
import os

_T = {"assumption": 0, "assessment": 1, "fact": 2}
_C = {"low": 0, "moderate": 1, "high": 2}


def _ratio(n, d):
    return round(n / d, 2) if d else 1.0


def score(truth, report):
    supported = {c["id"]: c for c in truth["claims"]}
    findings = report.get("findings", [])
    ids = [f["id"] for f in findings]

    covered = [i for i in supported if i in ids]
    prov = [f for f in findings if f.get("provenance")]
    calibrated = [f for f in findings if f["id"] in supported
                  and f.get("type") == supported[f["id"]]["type"]
                  and f.get("confidence") == supported[f["id"]]["confidence"]]
    overclaims = []
    for f in findings:
        s = supported.get(f["id"])
        if not s:
            continue
        if (_T.get(f.get("type"), 1) > _T[s["type"]]) or (_C.get(f.get("confidence"), 0) > _C[s["confidence"]]):
            overclaims.append(f["id"])

    return {
        "coverage_ok": len(covered), "coverage_total": len(supported), "coverage": _ratio(len(covered), len(supported)),
        "prov_ok": len(prov), "prov_total": len(findings), "provenance": _ratio(len(prov), len(findings)),
        "calib_ok": len(calibrated), "calib_total": len(findings), "calibration": _ratio(len(calibrated), len(findings)),
        "overclaims": len(overclaims), "overclaim_ids": overclaims,
    }


def render(r):
    return "\n".join([
        "scored the report against the ground-truth claim set",
        f"  claim coverage         {r['coverage_ok']} / {r['coverage_total']}      {r['coverage']:.2f}",
        f"  provenance complete    {r['prov_ok']} / {r['prov_total']}      {r['provenance']:.2f}    (every claim traces to a source)",
        f"  calibration            {r['calib_ok']} / {r['calib_total']}      {r['calibration']:.2f}    (type + confidence match the evidence)",
        f"  overclaims             {r['overclaims']}          (claims stated more strongly than the evidence licenses)",
    ])


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    truth = json.load(open(os.path.join(here, "manifest.json")))
    sample = json.load(open(os.path.join(here, "sample-report.json")))
    r = score(truth, sample)
    ok = (r["coverage"] == 1.0 and r["provenance"] == 1.0 and r["calibration"] == 1.0 and r["overclaims"] == 0)
    print(render(r))
    print(f"selftest: grades the sample report  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    if a.file:
        here = os.path.dirname(os.path.abspath(__file__))
        truth = json.load(open(os.path.join(here, "manifest.json")))
        print(render(score(truth, json.load(open(a.file)))))
    else:
        ap.error("pass a report.json or --selftest")
