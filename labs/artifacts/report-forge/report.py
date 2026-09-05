#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Assembling the intelligence report — Chapter 15 (Labs 15.4, 15.5, 15.6).

Assembles calibrated claims into a decision-ready product: a bottom line up front, key findings
ordered by confidence and tagged with type and source, an operator picture, a "what would change
this" section carrying each finding's falsifier, an evidence annex tracing every claim to the
engine that produced it, and an attribution boundary. The FULL assembler preserves all of it. The
NAIVE assembler is the report this chapter argues against — the careless write-up: it flattens
every claim to a flat, confident assertion, launders assessments and assumptions into "fact,"
raises every confidence to high, and drops provenance entirely, so a decision-maker cannot tell
what is load-bearing from what is a guess. The dangerous error of reporting is OVERCLAIMING, and
the naive assembler is a machine for it.
"""
import argparse
import json
import os

import claims as claims_mod
import evidence as evidence_mod

ORDER = {"high": 0, "moderate": 1, "low": 2}


def _flatten(c):
    # the confidence ratchet: everything becomes a sourceless, high-confidence fact
    return {**c, "type": "fact", "confidence": "high", "provenance": None, "falsifier": None}


def assemble(claims, naive=False):
    target = "Operator Alpha"
    if naive:
        findings = [_flatten(c) for c in claims]
        bluf = (f"{target} is behind a market vendor, two leak brands, and a forum handle; it lied about a "
                f"victim's data, published another, resurfaced under a new name, is being cloned, works in "
                f"UTC+2/+3, and is rebranding.")
        return {"target": target, "bluf": bluf, "findings": findings,
                "what_would_change": [], "annex": [], "boundary": None}

    findings = sorted(claims, key=lambda c: (ORDER[c["confidence"]], c["id"]))
    high = [c for c in findings if c["confidence"] == "high"]
    bluf = (f"With high confidence, {target} operates a market vendor and two leak brands under one signed "
            f"key and has resurfaced under a new persona after going dark; lower-confidence indicators point "
            f"to a rebrand in progress. Confidence and sourcing are stated per finding below.")
    return {
        "target": target,
        "bluf": bluf,
        "findings": findings,
        "what_would_change": [{"id": c["id"], "falsifier": c["falsifier"]} for c in findings if c["falsifier"]],
        "annex": [{"id": c["id"], "engine": c["provenance"]["engine"], "artifact": c["provenance"]["artifact"],
                   "why": c["provenance"]["why"]} for c in findings if c["provenance"]],
        "boundary": (f"This report attributes to {target} — a cluster of pseudonyms — at the confidence stated "
                     f"per finding. It does NOT identify a natural person; the step from an operator to a named "
                     f"individual is a legal and law-enforcement process, out of scope by design."),
    }


def render(rep, naive=False):
    L = []
    L.append(f"INTELLIGENCE BRIEF — {rep['target']}" + ("   [NAIVE ASSEMBLER]" if naive else ""))
    L.append("")
    L.append("BLUF: " + rep["bluf"])
    L.append("")
    L.append("KEY FINDINGS:")
    for c in rep["findings"]:
        tag = f"{c['type']}/{c['confidence']}"
        src = "" if naive or not c.get("provenance") else f"   (source: {c['provenance']['engine']}/{c['provenance']['artifact']})"
        L.append(f"  - [{tag:20}] {c['statement']}{src}")
    if rep.get("what_would_change"):
        L.append("")
        L.append("WHAT WOULD CHANGE THIS:")
        for w in rep["what_would_change"]:
            L.append(f"  - {w['id']}: {w['falsifier']}")
    if rep.get("annex"):
        L.append("")
        L.append("EVIDENCE ANNEX:")
        for a in rep["annex"]:
            L.append(f"  - {a['id']:16} <- {a['engine']}/{a['artifact']}")
    if rep.get("boundary"):
        L.append("")
        L.append("ATTRIBUTION BOUNDARY: " + rep["boundary"])
    if naive:
        L.append("")
        L.append("(no confidence tags beyond 'fact', no sourcing, no falsifiers, no boundary)")
    return "\n".join(L)


def run(naive=False):
    return assemble(claims_mod.build(evidence_mod.build()), naive=naive)


def selftest():
    cl = claims_mod.build(evidence_mod.build())
    full = assemble(cl, naive=False)
    naive = assemble(cl, naive=True)
    ok = True
    if not (full["annex"] and full["what_would_change"] and full["boundary"]):
        print("  full report must carry annex + falsifiers + boundary"); ok = False
    if not all(f["confidence"] in ("high", "moderate", "low") for f in full["findings"]):
        print("  full findings keep calibrated confidence"); ok = False
    if full["findings"][0]["confidence"] != "high":
        print("  full findings should lead with high confidence"); ok = False
    if any(f["provenance"] for f in naive["findings"]) or naive["annex"] or naive["boundary"]:
        print("  naive report should drop provenance, annex, and boundary"); ok = False
    if not all(f["confidence"] == "high" and f["type"] == "fact" for f in naive["findings"]):
        print("  naive report should flatten everything to high-confidence fact"); ok = False
    print(f"selftest: full report assembles {len(full['findings'])} findings with provenance, falsifiers,")
    print(f"          and a boundary; the naive assembler flattens them to sourceless fact  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    rep = run(naive=a.naive)
    print(json.dumps(rep, indent=2, default=str) if a.json else render(rep, naive=a.naive))
