#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Negotiation-channel extraction — Chapter 12 (Lab 12.5).

The private channel is where pressure is converted to payment, and a transcript is not a
number — it is an arc. Extraction recovers the opening demand, the offer trajectory as
the price falls, the proof exchanged, the settlement or its absence, and the tactics the
operator reaches for: deadline pressure, threats to leak or sell, threats to notify a
regulator or the press, an offer of proof, and the promise to delete the data. A scraper
that grabs the largest dollar figure learns almost nothing; the arc and the tactic set
are what characterise the operator and, in Lab 12.6, what the public claim is checked
against. The tactics are also identity: an operator's habitual sequence is a signature
Chapter 13 can match.
"""
import argparse
import glob
import os
import re
import sys

_TACTICS = {
    "deadline_pressure": r"within \d+\s*(day|hour)|in \d+\s*(day|hour)|deadline",
    "threat_leak": r"we (will )?publish|before we publish|\bleak\b|release the|go public",
    "threat_sell": r"\bsold\b|private buyer|auction|\bsell\b",
    "threat_notify": r"notify|regulator|GDPR|HIPAA|\bSEC\b|press|media|inform (the|your)",
    "proof_offered": r"\bproof\b|sample|decrypt(ed)? one",
    "deletion_promise": r"delete all|we will delete|\bwipe\b|erase",
}


def _header(text, field):
    m = re.search(r"^%s:\s*(.+)$" % re.escape(field), text, re.I | re.M)
    return m.group(1).strip() if m else None


def _operator_text(text):
    return " ".join(re.findall(r"operator:\s*(.+)", text, re.I))


def parse(text, naive=False):
    offers = [int(x) for x in re.findall(r"(\d+)\s*BTC", text)]
    settle_m = re.search(r"\[settlement\]\s*(\d+)\s*BTC", text, re.I)
    settlement = int(settle_m.group(1)) if settle_m else None

    if naive:                       # the brittle read: just the money
        return {"victim": _header(text, "victim"), "offers": offers, "settlement": settlement}

    op = _operator_text(text)
    tactics = sorted(t for t, pat in _TACTICS.items() if re.search(pat, op, re.I))

    proof_gb = None
    pm = re.search(r"proof[^\n]*?(\d+)\s*GB|(\d+)\s*GB\s*sample", text, re.I)
    if pm:
        proof_gb = float(pm.group(1) or pm.group(2))

    if re.search(r"\[settlement\]|settled", text, re.I):
        outcome = "settled"
    elif re.search(r"published", text, re.I):
        outcome = "published"
    elif re.search(r"ongoing", text, re.I):
        outcome = "ongoing"
    else:
        outcome = "unknown"

    return {
        "victim": _header(text, "victim"),
        "brand": _header(text, "brand"),
        "key": _header(text, "key"),
        "wallet": _header(text, "wallet"),
        "opening_demand": offers[0] if offers else None,
        "offers": offers,
        "settlement": settlement,
        "proof_gb": proof_gb,
        "tactics": tactics,
        "outcome": outcome,
    }


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    T = {os.path.basename(p): open(p).read()
         for p in glob.glob(os.path.join(here, "corpus", "nego-*.txt"))}
    ok = True

    n1 = parse(T["nego-1001.txt"])
    if not (n1["opening_demand"] == 100 and n1["settlement"] == 40 and n1["proof_gb"] == 12.0
            and n1["outcome"] == "settled"
            and set(n1["tactics"]) == {"deadline_pressure", "threat_leak", "proof_offered", "deletion_promise"}):
        print(f"  1001 -> {n1}")
        ok = False

    n2 = parse(T["nego-1002.txt"])
    if not (n2["outcome"] == "published" and "threat_notify" in n2["tactics"] and n2["settlement"] is None):
        print(f"  1002 -> {n2}")
        ok = False

    n4 = parse(T["nego-1004.txt"])
    if not (n4["outcome"] == "ongoing" and "threat_sell" in n4["tactics"]):
        print(f"  1004 -> {n4}")
        ok = False

    # the naive read gets a number and misses the arc entirely
    naive = parse(T["nego-1001.txt"], naive=True)
    if "tactics" in naive or naive["settlement"] != 40:
        print(f"  naive -> {naive}")
        ok = False

    print("selftest: transcripts parse to an arc — opening, offers, proof, settlement, tactics,")
    print(f"          outcome — where the naive read sees only a dollar figure  -> {'PASS' if ok else 'FAIL'}")
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
        files = sorted(glob.glob(os.path.join(a.corpus, "nego-*.txt")))
        if a.summary:
            for p in files:
                n = parse(open(p).read())
                print(f"    {n['victim']:24} demand {n['opening_demand']} -> settle {n['settlement']}  "
                      f"[{n['outcome']}]  tactics: {', '.join(n['tactics'])}")
        else:
            import json
            print(json.dumps({os.path.basename(p): parse(open(p).read()) for p in files}, indent=2))
    else:
        ap.error("use --selftest or --corpus <dir>")
