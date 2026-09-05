#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Builds the leak-lab corpus — an extortion operation across two surfaces, for Chapter 12.

A dedicated leak site (DLS) captured at two points in time, a rebrand site that reposts
two of its victims, one markup-drift victim entry, and negotiation transcripts for four
victims. The corpus is built so the higher-order signals have ground truth: a victim
whose entry is unchanged between snapshots is byte-identical (the store collapses it), a
deadline that slides between snapshots is countdown theater, a victim that quietly
disappears was paid or pulled, a reposted victim with the same claim is affiliate
movement (a mirror) while one with an inflated claim is a recycled clone, and a public
claim that the private transcript contradicts is a bluff. Every page and transcript is
watermarked synthetic — invented groups, fake victims, placeholder volumes, fake keys
and wallets. Run once to (re)generate corpus/.
"""
import os

CSS = "/assets/dls.4c1e.css"
WM = '<div class=wm>SYNTHETIC LAB DATA</div>'
KEY = "F19B7A0C4E82D5613FA0"      # fake operator PGP fingerprint (reused across brands = a tell)
WALLET = "bc1qsynth0laba0000000000000000000000zzzz"   # fake wallet

def head(brand, t):
    return (f"<!DOCTYPE html><html><head><link rel=stylesheet href='{CSS}'>"
            f"<title>SYNTHETIC — {t}</title></head><body>{WM}"
            f"<header><span class=brand>{brand}</span>"
            "<nav><a href='/'>victims</a><a href='/about'>about</a></nav></header>")

FOOT = "</body></html>"


def victim_entry(brand, vid, org, sector, country, gb, proof, status, deadline, drift=False):
    if not drift:
        body = (
            f"<main><h1 class=v-org>{org}</h1>"
            "<table class=v-meta><tbody>"
            f"<tr><td>Sector</td><td class=f-sector>{sector}</td></tr>"
            f"<tr><td>Country</td><td class=f-country>{country}</td></tr>"
            f"<tr><td>Data</td><td class=f-volume>{gb} GB</td></tr>"
            f"<tr><td>Proof</td><td class=f-proof>{proof}</td></tr>"
            f"<tr><td>Status</td><td class=f-status>{status}</td></tr>"
            f"<tr><td>Deadline</td><td class=f-deadline>{deadline}</td></tr>"
            "</tbody></table>"
            f"<div class=v-id data-id='{vid}'>Entry #{vid}</div></main>")
    else:
        body = (
            f"<main><h2 class=org>{org}</h2>"
            "<dl class=meta>"
            f"<dt>Sector</dt><dd>{sector}</dd>"
            f"<dt>Country</dt><dd>{country}</dd>"
            f"<dt>Data</dt><dd>{gb} GB</dd>"
            f"<dt>Proof</dt><dd>{proof}</dd>"
            f"<dt>Status</dt><dd>{status}</dd>"
            f"<dt>Deadline</dt><dd>{deadline}</dd>"
            "</dl>"
            f"<p class=ref>Entry #{vid}</p></main>")
    return head(brand, "Victim") + body + FOOT


def index(brand, rows):
    items = "".join(f"<li><a href='/v/{vid}'>{org}</a> — <span class=st>{status}</span></li>"
                    for vid, org, status in rows)
    return head(brand, "Index") + f"<main><h1>{brand} — victims</h1><ul class=victims>{items}</ul></main>" + FOOT


# ---- canonical victims, with per-snapshot status/deadline ----
V = {
    1001: dict(org="Northwind Logistics", sector="Manufacturing", country="US", gb=200,
               proof="12GB sample tree",
               t1=("countdown", "2026-08-05"), t2=("countdown", "2026-08-12")),   # deadline SLID
    1002: dict(org="Meridian Health", sector="Healthcare", country="UK", gb=500,
               proof="patient index, 3 files",
               t1=("countdown", "2026-08-03"), t2=("published", "2026-08-03")),   # PUBLISHED
    1003: dict(org="Coastal Credit Union", sector="Finance", country="CA", gb=80,
               proof="loan records sample",
               t1=("teased", "—"), t2=("withdrawn", "—")),                        # WITHDRAWN (quiet)
    1004: dict(org="Apex Retail Group", sector="Retail", country="US", gb=1000,
               proof="POS logs sample",
               t1=("sold", "—"), t2=("sold", "—")),                               # SOLD (unchanged -> collapses)
    1005: dict(org="GraniteWorks Foundry", sector="Manufacturing", country="US", gb=50,
               proof="CAD archive sample",
               t1=("teased", "—"), t2=("countdown", "2026-08-20")),               # teased -> countdown
}

SITE_A = "RedLattice"
SITE_B = "BlackVault"      # a rebrand / affiliate surface

pages = {}

# Site A, two snapshots
for snap in ("t1", "t2"):
    rows = []
    for vid, d in V.items():
        status, deadline = d[snap]
        pages[f"a-{snap}-{vid}.html"] = victim_entry(SITE_A, vid, d["org"], d["sector"],
                                                      d["country"], d["gb"], d["proof"], status, deadline)
        rows.append((vid, d["org"], status))
    pages[f"a-{snap}-index.html"] = index(SITE_A, rows)

# a markup-drift variant of one t2 entry (fields moved out of the table)
d = V[1003]
pages["a-t2-1003-drift.html"] = victim_entry(SITE_A, 1003, d["org"], d["sector"], d["country"],
                                             d["gb"], d["proof"], d["t2"][0], d["t2"][1], drift=True)

# Site B reposts: 1004 with the SAME claim (mirror = affiliate movement),
# 1005 with an INFLATED claim (clone = recycled)
d = V[1004]
pages["b-1004.html"] = victim_entry(SITE_B, 1004, d["org"], d["sector"], d["country"],
                                     d["gb"], d["proof"], "sold", "—")
d = V[1005]
pages["b-1005.html"] = victim_entry(SITE_B, 1005, d["org"], d["sector"], d["country"],
                                     150, d["proof"], "countdown", "2026-08-20")   # 150GB vs 50GB

# ---- negotiation transcripts (plain text) ----
def transcript(org, brand, lines):
    hdr = (f"=== SYNTHETIC LAB DATA — negotiation transcript ===\n"
           f"victim: {org}\nbrand: {brand}\nkey: {KEY}\nwallet: {WALLET}\n\n")
    return hdr + "\n".join(lines) + "\n"

nego = {}

nego["nego-1001.txt"] = transcript("Northwind Logistics", SITE_A, [
    "[2026-07-20 10:00] operator: Your network is encrypted. We hold 200GB. Pay 100 BTC within 5 days or we publish.",
    "[2026-07-21 09:00] victim: We need proof and more time.",
    "[2026-07-21 12:00] operator: proof: 12GB sample tree attached. Decrypt one file to verify.",
    "[2026-07-25 10:00] operator: We can extend the deadline to Aug 12. Price now 60 BTC.",
    "[2026-07-28 15:00] victim: We can do 40.",
    "[2026-07-29 11:00] operator: Agreed. 40 BTC. Send to the wallet and we delete all data.",
    "[settlement] 40 BTC — settled",
])

nego["nego-1002.txt"] = transcript("Meridian Health", SITE_B and SITE_A, [
    "[2026-07-18 08:00] operator: 500GB of patient records. 300 BTC or we publish and notify the regulator under GDPR and HIPAA.",
    "[2026-07-19 09:00] victim: This is not payable.",
    "[2026-07-20 10:00] operator: Then we inform the press and your regulator. Deadline Aug 3.",
    "[2026-07-30 10:00] victim: We will not pay.",
    "[outcome] no settlement — published",
])

nego["nego-1003.txt"] = transcript("Coastal Credit Union", SITE_A, [
    "[2026-07-15 10:00] operator: We have 80GB. 100 BTC before we publish.",
    "[2026-07-16 09:00] victim: Prove it and we will talk.",
    "[2026-07-16 12:00] operator: proof: we decrypted one loan file, see attached.",
    "[2026-07-22 10:00] operator: Final price 40 BTC. Pay and we will delete all data, you have our word.",
    "[2026-07-24 11:00] victim: Paid.",
    "[settlement] 40 BTC — settled",
])

nego["nego-1004.txt"] = transcript("Apex Retail Group", SITE_A, [
    "[2026-07-10 10:00] operator: 1TB of your data is already sold to a private buyer.",
    "[2026-07-11 09:00] victim: Then what do you want from us.",
    "[2026-07-11 12:00] operator: We can still pull it from the buyer for 200 BTC before it spreads.",
    "[2026-07-14 10:00] operator: Deadline in 3 days or it goes to auction as well.",
    "[outcome] ongoing",
])

here = os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(here, "corpus")
os.makedirs(outdir, exist_ok=True)
for name, html in pages.items():
    with open(os.path.join(outdir, name), "w") as fh:
        fh.write(html)
for name, text in nego.items():
    with open(os.path.join(outdir, name), "w") as fh:
        fh.write(text)
print(f"wrote {len(pages)} DLS pages + {len(nego)} transcripts to {outdir}")
