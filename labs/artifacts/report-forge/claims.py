#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Claims and calibrated confidence — Chapter 15 (Labs 15.1, 15.3).

A report is a chain of claims, and this turns the evidence graph into them. Every claim carries
four things a decision-maker needs: a statement, its TYPE (fact — an observed event; assessment
— an analytic judgement; or assumption — a working premise), its PROVENANCE (which engine and
artifact it rests on), and a CONFIDENCE set by one rule, not by how sure the analyst feels. The
rule is the discipline the whole book has been building toward: a claim resting on a HARD
identifier (a shared signed key, a signed-key watchlist match) or on an OBSERVED event is high;
one resting on several INDIRECT signals is moderate; one resting on a SINGLE SOFT signal — an
activity-rhythm timezone hint — is low. Confidence is inherited from the upstream engine that
emits one (a cluster's high, an alert's severity) and never raised above it. Each claim also
carries a FALSIFIER — the evidence that would overturn it — because a claim a decision-maker
cannot argue with is not intelligence, it is an assertion.
"""
import argparse
import json
import os

import evidence as evidence_mod

# the provenance -> confidence rule, made explicit
BASIS_CONF = {
    "hard_identifier": "high",   # shared signed key / wallet / signed-key watchlist match
    "observed_event": "high",    # a publication, a clone appearing on the range
    "indirect_signals": "moderate",  # several circumstantial signals, no direct evidence
    "single_soft_signal": "low", # one soft signal (rhythm) — a hint, not a finding
}


def _c(basis):
    return BASIS_CONF[basis]


def build(graph):
    g = graph
    personas = g["cluster"]["personas"]
    op = g["operator"]
    market = g["market"]["vendor"]
    leak_brands = [p for p in personas if p in ("RedLattice", "BlackVault")]
    nw = g["leak"]["bluffs"].get("1001", {})
    pub = g["leak"]["published"][0]["org"] if g["leak"]["published"] else "a victim"
    resurf = g["detection"]["resurface"]["name"]
    clone = g["detection"]["clone"]["name"]
    framers = g["framing"]

    claims = []

    def add(cid, statement, ctype, basis, engine, artifact, why, falsifier):
        claims.append({"id": cid, "statement": statement, "type": ctype,
                       "confidence": _c(basis), "basis": basis,
                       "provenance": {"engine": engine, "artifact": artifact, "why": why},
                       "falsifier": falsifier})

    add("identity",
        f"Operator {op} operates the market vendor {market}, the leak brands "
        f"{' and '.join(leak_brands)}, and the forum persona n1ghthawk.",
        "assessment", "hard_identifier", "persona-linkage", "fuse",
        f"one signed key ({g['identity_key']}) and a shared wallet control all four personas",
        "the shared key is shown to be displayed-not-controlled on one of the brands")

    add("volume_bluff",
        f"{op} inflated its extortion of {nw.get('org','Northwind Logistics')} — claiming far more "
        f"data publicly than it proved privately (a volume bluff).",
        "assessment", "hard_identifier", "leak-negotiation", "correlate",
        "the public claim exceeds the privately proven sample by more than fivefold",
        "a fuller proof surfaces that matches the public claim")

    add("follow_through",
        f"{op} published {pub} after threatening regulator notification; that threat was carried "
        f"out and was not a bluff.",
        "fact", "observed_event", "leak-negotiation", "lifecycle",
        "the victim's status moved from countdown to published across the snapshots",
        "the published archive proves fabricated or recycled")

    add("resurface",
        f"{op} has resurfaced under the new forum persona {resurf}, signing with the key it is "
        f"already known by, after its market went dark.",
        "assessment", "hard_identifier", "detection", "operator_resurface",
        "the new persona's signed key matches the watched operator's key",
        f"the key on {resurf} proves stolen or merely displayed, not controlled")

    add("clone",
        f"A clone, {clone}, is impersonating {op}'s market using a swapped key and wallet.",
        "fact", "observed_event", "detection", "new_clone",
        "a look-alike site appeared carrying a different key from the original",
        f"the swapped key on {clone} proves to be {op} rotating its own infrastructure")

    add("timezone",
        f"{op}'s operator likely works in a UTC+2 to UTC+3 timezone band.",
        "assessment", "single_soft_signal", "persona-linkage", "behavior",
        "the activity-rhythm histogram clusters in those hours — a hint, not a fingerprint",
        "activity spreads across the histogram, or scheduled automation is evident")

    add("rebrand",
        f"{op}'s market going dark together with the appearance of a clone suggests a possible "
        f"rebrand or infrastructure migration in progress.",
        "assessment", "indirect_signals", "detection", "market_down + new_clone",
        "two circumstantial signals point the same way, with no direct evidence of intent",
        "the original market returns unchanged and the clone is abandoned")

    if framers:
        add("do_not_attribute",
            f"The persona {' and '.join(framers)} displays {op}'s key but signs its own; it is a "
            f"separate operator, and its activity must not be attributed to {op}.",
            "assessment", "hard_identifier", "persona-linkage", "framing_flags",
            "a displayed key is not a control proof; merging on it would be a false accusation",
            f"{' and '.join(framers)} is shown to sign with {op}'s key")

    return claims


def selftest():
    claims = build(evidence_mod.build())
    ok = True
    by = {c["id"]: c for c in claims}
    if by["timezone"]["confidence"] != "low":
        print(f"  timezone (single soft signal) should be low -> {by['timezone']['confidence']}"); ok = False
    if by["rebrand"]["confidence"] != "moderate":
        print(f"  rebrand (indirect signals) should be moderate -> {by['rebrand']['confidence']}"); ok = False
    if by["identity"]["confidence"] != "high" or by["identity"]["type"] != "assessment":
        print(f"  identity should be a high-confidence assessment -> {by['identity']}"); ok = False
    if by["follow_through"]["type"] != "fact":
        print(f"  follow_through should be a fact -> {by['follow_through']['type']}"); ok = False
    if not all(c["provenance"]["engine"] for c in claims):
        print("  every claim must carry provenance"); ok = False
    if not all(c["falsifier"] for c in claims):
        print("  every claim must carry a falsifier"); ok = False
    if "do_not_attribute" not in by:
        print("  the do-not-attribute negative finding should be present"); ok = False
    n = {"high": 0, "moderate": 0, "low": 0}
    for c in claims:
        n[c["confidence"]] += 1
    print(f"selftest: {len(claims)} claims built from the graph, each with provenance, type, and a")
    print(f"          calibrated confidence ({n['high']} high / {n['moderate']} moderate / {n['low']} low)  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    claims = build(evidence_mod.build())
    if a.summary:
        for c in claims:
            print(f"    [{c['confidence']:8} {c['type']:10}] {c['id']:16} <- {c['provenance']['engine']}/{c['provenance']['artifact']}")
    else:
        print(json.dumps(claims, indent=2, default=str))
