#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Builds the clone-lab corpus: a set of pages designed to break exact-hash
dedup. Same-operator mirrors (exact + near-duplicate), impersonating clones
(payment-swapped + reworded-keyless), a genuinely different service on the same
open-source template (the false-merge trap), and two unrelated families. Run once
to (re)generate labs/artifacts/dedup/corpus/. Ground truth lives in the dedup-scorer
manifest. Every page is watermarked synthetic — invented vendors, fake keys."""
import os

MARKET_CSS = "/assets/app.7f3a2c.css"
MARKET_LOGO = "/assets/logo.9b1d4e.png"
K1_PGP, K1_BTC = "9A3F1C4D7E20BQ", "bc1q_market_k7"
K2_PGP, K2_BTC = "2E77A0B9C31DFP", "bc1q_clone_z9"

# the market template T — header, listings table, contact block
def market_page(listings, css=MARKET_CSS, logo=MARKET_LOGO, pgp=K1_PGP, btc=K1_BTC,
                banner="", contact=True):
    rows = "".join(
        f"<tr><td class=v>{v}</td><td class=p>{p}</td><td class=c>{c}</td></tr>"
        for v, p, c in listings)
    contact_html = (
        f"<section class=contact><h2>Vendor contact</h2>"
        f"<p>Escrow PGP {pgp}</p><p>Deposit address {btc}</p></section>"
        if contact else
        "<section class=contact><h2>Vendor contact</h2>"
        "<p>Escrow details on request after account approval.</p></section>")
    return (
        "<!DOCTYPE html><html><head>"
        f"<link rel=stylesheet href='{css}'>"
        "<title>SYNTHETIC — Market</title></head><body>"
        f"<div class=wm>SYNTHETIC LAB DATA</div>"
        f"<header><img src='{logo}' alt=logo><h1>The Bazaar</h1>"
        "<nav><a href='/'>home</a><a href='/listings'>listings</a>"
        "<a href='/vendors'>vendors</a></nav></header>"
        f"{banner}"
        "<main><h2>Current listings</h2>"
        "<table class=listings><thead><tr><th>vendor</th><th>product</th>"
        f"<th>terms</th></tr></thead><tbody>{rows}</tbody></table></main>"
        f"{contact_html}</body></html>")

# the canonical market's listings (vendor, product, terms) — content C1
C1 = [
    ("NightHawk", "hardware wallet, sealed", "ships worldwide, escrow"),
    ("PaperTrail", "novelty ID template pack", "digital delivery, no refunds"),
    ("GreyOwl", "encrypted phone, wiped", "EU only, finalize early"),
    ("SaltMine", "gift card codes, bulk", "instant, tiered pricing"),
]
# reworded listings — same items and topics, different words (content C2, keyless clone)
C2 = [
    ("NightHawk", "sealed cold-storage wallet unit", "global shipping with escrow held"),
    ("PaperTrail", "template bundle for novelty identification", "sent digitally, sales final"),
    ("GreyOwl", "securely wiped encrypted handset", "Europe only, release funds up front"),
    ("SaltMine", "wholesale prepaid card numbers", "delivered instantly, priced by tier"),
]
# a genuinely different market on the SAME template — different content C3 (the trap)
C3 = [
    ("BlueReef", "aquarium livestock, rare coral", "temperature-controlled shipping"),
    ("Cobbler", "handmade leather boots", "made to order, 3 week lead"),
    ("Verdant", "heirloom seed collections", "seasonal, germination guaranteed"),
    ("Tinker", "vintage watch movements", "as-is, no returns"),
]

FORUM_CSS = "/assets/forum.aa11bb.css"
def forum_page(banner=""):
    return (
        "<!DOCTYPE html><html><head>"
        f"<link rel=stylesheet href='{FORUM_CSS}'>"
        "<title>SYNTHETIC — Forum</title></head><body>"
        "<div class=wm>SYNTHETIC LAB DATA</div>"
        "<header><h1>The Commons</h1><nav><a href='/new'>newest</a>"
        "<a href='/top'>top</a></nav></header>"
        f"{banner}"
        "<main><ul class=threads>"
        "<li><a href='/t/1'>vendor vouches and scam reports</a><span>142</span></li>"
        "<li><a href='/t/2'>opsec for first-time buyers</a><span>88</span></li>"
        "<li><a href='/t/3'>which escrow do you trust</a><span>203</span></li>"
        "</ul></main></body></html>")

def paste_page():
    return (
        "<!DOCTYPE html><html><head>"
        "<link rel=stylesheet href='/assets/paste.cc22dd.css'>"
        "<title>SYNTHETIC — Paste</title></head><body>"
        "<div class=wm>SYNTHETIC LAB DATA</div>"
        "<main><h1>untitled paste</h1><pre>"
        "no real breach data — placeholder dump for the lab\n"
        "record 0001 redacted\nrecord 0002 redacted</pre></main></body></html>")

BANNER = "<div class=notice>Mirror synced 2026-07-30 14:22 UTC — bookmark this address.</div>"

pages = {
    # market family (ground-truth cluster "market")
    "market.html": market_page(C1),
    "market-mirror-exact.html": market_page(C1),                        # byte-identical
    "market-mirror-banner.html": market_page(C1, banner=BANNER),        # near-dup mirror
    "market-clone-keyswap.html": market_page(C1, pgp=K2_PGP, btc=K2_BTC),  # payment-swapped clone (reused assets)
    "market-clone-keyless.html": market_page(C2, contact=False),        # reworded, no keys, but SAME assets (scraped)
    # the false-merge trap: same template, different everything
    "other-market.html": market_page(C3, css="/assets/app.3e9f01.css",
                                      logo="/assets/logo.c4a7b2.png",
                                      pgp="7C10FF93AB24EE", btc="bc1q_reef_m3"),
    # unrelated family (cluster "forum")
    "forum.html": forum_page(),
    "forum-mirror.html": forum_page(banner="<div class=notice>Mirror of The Commons.</div>"),
    # singleton (cluster "paste")
    "paste.html": paste_page(),
}

here = os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(here, "corpus")
os.makedirs(outdir, exist_ok=True)
for name, html in pages.items():
    with open(os.path.join(outdir, name), "w") as fh:
        fh.write(html)
print(f"wrote {len(pages)} corpus pages to {outdir}")
