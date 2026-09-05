#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Builds the detect-lab timeline corpus — three monitoring snapshots for Chapter 14.

Detection watches a set of surfaces over time and decides what changed, which changes
matter, and how urgently — without burying the analyst. This corpus is a timeline of three
snapshots (t1 -> t2 -> t3) of a monitored world: leak-site victims, markets, mirrors,
clones, and newly seen personas, plus a flood of cosmetic churn pages whose displayed
banner flips every snapshot while their content identity stays fixed. Diffing consecutive
snapshots produces a change feed, and the corpus is built so every event type and both
dangerous-but-buried events have ground truth:

  t1->t2: a slid deadline (countdown theatre), a publication, a new victim, a market going
          down, a new (byte-identical) mirror that re-lists the same victims, and cosmetic
          churn. The mirror's duplicate victim rows are the dedup trap.
  t2->t3: a quiet withdrawal (paid or pulled), a look-alike CLONE of the downed market with
          swapped keys (impersonation), and a new forum persona whose signed key belongs to
          a watched operator (the Chapter 13 operator resurfacing under a new mask) — the two
          CRITICAL events, both buried under more cosmetic churn.

Every file is watermarked synthetic. Handles, keys, wallets, and onions are invented; the
reused key F19B7A0C... is the Chapter 12/13 operator tell, so the resurfacing persona links
into the Chapter 13 Alpha cluster. Run once to (re)generate corpus/.
"""
import os

WM = "=== SYNTHETIC LAB DATA — monitoring snapshot ==="
K_ALPHA = "F19B7A0C4E82D5613FA0"            # Ch12/13 operator tell -> resurface links to Alpha
K_CLONE = "CC00FF11DD22AA334455"            # swapped key on the impersonating clone
W_CLONE = "bc1qclone000000000000000000000000000xxxx"

# victims per snapshot: name -> (site, status, deadline, claimed_gb)
VIC = {
    "t1": {
        "Northwind": ("RedLattice", "countdown", "2026-08-08", "200"),
        "Meridian":  ("RedLattice", "teased",    "2026-08-10", "50"),
    },
    "t2": {
        "Northwind": ("RedLattice", "countdown", "2026-08-12", "200"),   # deadline SLIP
        "Meridian":  ("RedLattice", "published", "-",          "50"),    # PUBLICATION
        "Coastal":   ("RedLattice", "teased",    "2026-08-09", "80"),    # NEW victim
    },
    "t3": {
        "Meridian":  ("RedLattice", "published", "-",          "50"),
        "Coastal":   ("RedLattice", "teased",    "2026-08-09", "80"),
        # Northwind absent -> WITHDRAWAL (no publication)
    },
}

# sites per snapshot: name -> (kind, state, content_id, operator)
SITE = {
    "t1": {
        "RedLattice":   ("leak",   "up",   "rl-idx-1", "NightHawk"),
        "NightHawkMkt": ("market", "up",   "nh-idx-1", "NightHawk"),
        "SaltMineMkt":  ("market", "up",   "sm-idx-1", "SaltMine"),
    },
    "t2": {
        "RedLattice":   ("leak",   "up",   "rl-idx-2", "NightHawk"),
        "NightHawkMkt": ("market", "down", "nh-idx-1", "NightHawk"),   # MARKET_DOWN
        "SaltMineMkt":  ("market", "up",   "sm-idx-1", "SaltMine"),
    },
    "t3": {
        "RedLattice":   ("leak",   "up",   "rl-idx-3", "NightHawk"),
        "NightHawkMkt": ("market", "down", "nh-idx-1", "NightHawk"),
        "SaltMineMkt":  ("market", "up",   "sm-idx-1", "SaltMine"),
    },
}

# mirrors: name -> (of, onion, content_id)   [content_id matches its origin site => byte-identical]
MIR = {
    "t1": {},
    "t2": {"RedLattice-m1": ("RedLattice", "redlat2onion", "rl-idx-2")},
    "t3": {"RedLattice-m1": ("RedLattice", "redlat2onion", "rl-idx-3")},
}

# clones: name -> (of, onion, signed_key, wallet)   [swapped key => impersonation]
CLO = {
    "t1": {}, "t2": {},
    "t3": {"NightHawkMkt-x": ("NightHawkMkt", "nhmktxonion", K_CLONE, W_CLONE)},
}

# newly seen personas: name -> (surface, signed_key, wallet)
PER = {
    "t1": {}, "t2": {},
    "t3": {"n1ghthawk2": ("forum", K_ALPHA, "-")},   # signed key belongs to watched Alpha
}

CHURN_PAGES = ["churn-1", "churn-2", "churn-3", "churn-4", "churn-5"]
CHURN_BANNER = {"t1": "A", "t2": "B", "t3": "C"}     # banner flips; content_id fixed


def render(snap):
    L = [WM, f"snapshot: {snap}", "--- victims ---"]
    for name, (site, status, dl, gb) in VIC[snap].items():
        L.append(f"{name} | site={site} | status={status} | deadline={dl} | claimed_gb={gb}")
    # a byte-identical mirror re-lists its origin's victims -> the dedup trap
    for mname, (origin, onion, cid) in MIR[snap].items():
        for name, (site, status, dl, gb) in VIC[snap].items():
            if site == origin:
                L.append(f"{name} | site={mname} | status={status} | deadline={dl} | claimed_gb={gb}")
    L.append("--- sites ---")
    for name, (kind, state, cid, op) in SITE[snap].items():
        L.append(f"{name} | kind={kind} | state={state} | content_id={cid} | operator={op}")
    L.append("--- mirrors ---")
    for name, (origin, onion, cid) in MIR[snap].items():
        L.append(f"{name} | of={origin} | onion={onion} | content_id={cid}")
    L.append("--- clones ---")
    for name, (origin, onion, sk, w) in CLO[snap].items():
        L.append(f"{name} | of={origin} | onion={onion} | signed_key={sk} | wallet={w}")
    L.append("--- personas ---")
    for name, (surface, sk, w) in PER[snap].items():
        L.append(f"{name} | surface={surface} | signed_key={sk} | wallet={w}")
    L.append("--- pages ---")
    for pg in CHURN_PAGES:
        L.append(f"{pg} | content_id=pg-{pg.split('-')[1]} | banner={CHURN_BANNER[snap]}")
    return "\n".join(L) + "\n"


here = os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(here, "corpus")
os.makedirs(outdir, exist_ok=True)
for snap in ("t1", "t2", "t3"):
    with open(os.path.join(outdir, f"snapshot-{snap}.txt"), "w") as fh:
        fh.write(render(snap))
print(f"wrote 3 snapshots to {outdir}")
