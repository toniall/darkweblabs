#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""The evidence graph — Chapter 15 (Lab 15.2), the capstone run.

This is where the whole book runs end-to-end. It chains the four attribution engines — Chapter
11's market extractor, Chapter 12's leak/negotiation cross-check, Chapter 13's persona fusion,
and Chapter 14's detection monitor — over one incident and assembles their real outputs into a
single evidence graph for one operator. Each engine is RUN, not mocked: because the engines
share module names (every one has a pipeline.py), they are executed in their own processes and
their JSON is read back, so the graph is built from exactly what the tools produce. The graph
is keyed by the operator tell carried across Part IV — the reused signed key F19B7A0C… — which
is what lets a market vendor, two leak brands, a forum handle, and a detection alert be assembled
as facets of the same operator. Nothing here re-derives attribution; it consumes it. Every
corpus is watermarked synthetic, so the operator assembled is a codename over invented personas,
never a real person.
"""
import argparse
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
TELL = "F19B7A0C4E82D5613FA0"   # Ch12/13 operator tell — the key the graph is assembled around
CODENAME = "Alpha"              # analyst codename for the high-confidence cluster (op-1)


def _run(engine_dir, code):
    """Run one engine in its own process and return its parsed JSON output."""
    r = subprocess.run(["python3", "-c", code], cwd=os.path.join(ART, engine_dir),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{engine_dir}: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout)


def _persona():
    return _run("persona-extract",
                "import fuse,identifiers,json;"
                "print(json.dumps(fuse.fuse(identifiers.load('corpus')),default=str))")


def _leak():
    return _run("leak-extract", "import pipeline,json;print(json.dumps(pipeline.run('corpus'),default=str))")


def _market():
    return _run("market-extract", "import pipeline,json;print(json.dumps(pipeline.run('corpus'),default=str))")


def _detect():
    return _run("detect-monitor", "import pipeline,json;print(json.dumps(pipeline.run('corpus'),default=str))")


def build():
    persona, leak, market, detect = _persona(), _leak(), _market(), _detect()

    # 1) the operator identity: the one high-confidence cluster, held by hard identifiers
    cluster = next(c for c in persona["clusters"] if c["confidence"] == "high")
    framing = persona.get("framing_flags", [])

    # 2) leak facets: which victims Alpha bluffed, which threat it carried out
    bluffs = {v: d for v, d in leak["bluffs"].items() if d.get("bluffs")}
    published = [d for d in leak["lifecycle"].values() if d.get("to_status") == "published"]

    # 3) market facet: Alpha's vendor handle present in the market graph
    vendor = next((v for v in market["vendors"] if v.get("handle") in cluster["personas"]), None)

    # 4) detection facets: the resurface and the impersonating clone
    resurface = next((a for a in detect["alerts"] if a["type"] == "operator_resurface"), None)
    clone = next((a for a in detect["alerts"] if a["type"] == "new_clone"), None)

    # framers: personas OUTSIDE the cluster that display a cluster member's key (displayed != controlled)
    members = set(cluster["personas"])
    framers = set()
    for f in framing:
        a, b = f.get("a"), f.get("b")
        if a in members and b not in members:
            framers.add(b)
        elif b in members and a not in members:
            framers.add(a)

    return {
        "operator": CODENAME,
        "identity_key": TELL,
        "cluster": {"personas": cluster["personas"], "confidence": cluster["confidence"],
                    "signals": cluster["signals"]},
        "market": {"vendor": vendor["handle"] if vendor else None},
        "leak": {"bluffs": bluffs, "published": published},
        "detection": {"resurface": resurface, "clone": clone},
        "framing": sorted(framers),
    }


def selftest():
    g = build()
    ok = True
    if g["cluster"]["confidence"] != "high" or "shared_signed_key" not in g["cluster"]["signals"]:
        print(f"  Alpha cluster should be high, held by a signed key -> {g['cluster']}"); ok = False
    if not {"NightHawk", "RedLattice", "BlackVault"} <= set(g["cluster"]["personas"]):
        print(f"  Alpha personas -> {g['cluster']['personas']}"); ok = False
    if "1001" not in g["leak"]["bluffs"] or "volume_bluff" not in g["leak"]["bluffs"]["1001"]["bluffs"]:
        print(f"  Northwind volume bluff missing -> {g['leak']['bluffs']}"); ok = False
    if not g["leak"]["published"]:
        print("  a followed-through publication should be present"); ok = False
    if g["market"]["vendor"] != "NightHawk":
        print(f"  Alpha's market vendor -> {g['market']['vendor']}"); ok = False
    if not (g["detection"]["resurface"] and g["detection"]["clone"]):
        print("  resurface + clone alerts should be present"); ok = False
    if not g["framing"]:
        print("  the Mimic displayed-key framing flag should carry through"); ok = False
    print(f"selftest: the four engines run and assemble into one evidence graph for Operator")
    print(f"          {g['operator']}, keyed by the reused signed key  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    g = build()
    if a.summary:
        print(f"    operator: {g['operator']}  (key {g['identity_key']})")
        print(f"    cluster:  {', '.join(g['cluster']['personas'])}  [{g['cluster']['confidence']}]")
        print(f"    market:   vendor {g['market']['vendor']}")
        print(f"    leak:     bluffed victims {list(g['leak']['bluffs'])}, published {[p['org'] for p in g['leak']['published']]}")
        print(f"    detect:   resurface {g['detection']['resurface']['name']}, clone {g['detection']['clone']['name']}")
        print(f"    framing:  {g['framing']} display Alpha's key but do not control it (do not attribute)")
    else:
        print(json.dumps(g, indent=2, default=str))
