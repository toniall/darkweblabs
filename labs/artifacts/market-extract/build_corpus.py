#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Builds the market-lab corpus — a synthetic market's pages for Chapter 11.

Category index and detail pages, vendor profiles, one markup-drift variant (fields
moved out of the table so a brittle scraper misses them), and the adversarial and
defensive cases the extractor must survive: a scam bait-price listing, a resale ring
(one listing posted by two vendors), a gamed-reputation vendor, a borrowed-key vendor
impersonating another, a CAPTCHA wall, a rate-limit response, a poisoned catalogue
served to a flagged account, and a honeypot link. Every page is watermarked synthetic
— invented vendors, fake keys, placeholder listings. Run once to (re)generate corpus/.
"""
import os

CSS = "/assets/market.7f3a2c.css"
WM = '<div class=wm>SYNTHETIC LAB DATA</div>'

def head(t):
    return (f"<!DOCTYPE html><html><head><link rel=stylesheet href='{CSS}'>"
            f"<title>SYNTHETIC — {t}</title></head><body>{WM}"
            "<header><a href='/'>home</a><nav><a href='/c/hardware'>hardware</a>"
            "<a href='/c/digital'>digital</a><a href='/vendors'>vendors</a></nav></header>")

FOOT = "</body></html>"


def listing(lid, title, vendor, category, price, cur, sfrom, sto, terms, drift=False):
    if not drift:
        body = (
            f"<main><h1 class=listing-title>{title}</h1>"
            "<table class=listing-meta><tbody>"
            f"<tr><td>Vendor</td><td class=f-vendor>{vendor}</td></tr>"
            f"<tr><td>Category</td><td class=f-category>{category}</td></tr>"
            f"<tr><td>Price</td><td class=f-price>{price} {cur}</td></tr>"
            f"<tr><td>Ships from</td><td class=f-from>{sfrom}</td></tr>"
            f"<tr><td>Ships to</td><td class=f-to>{sto}</td></tr>"
            f"<tr><td>Terms</td><td class=f-terms>{terms}</td></tr>"
            "</tbody></table>"
            f"<div class=listing-id data-id='{lid}'>Listing #{lid}</div></main>")
    else:
        # same data, drifted markup: a definition list, no f-* classes, "Label: value"
        body = (
            f"<main><h2 class=title>{title}</h2>"
            "<dl class=meta>"
            f"<dt>Vendor</dt><dd>{vendor}</dd>"
            f"<dt>Category</dt><dd>{category}</dd>"
            f"<dt>Price</dt><dd>{price} {cur}</dd>"
            f"<dt>Ships from</dt><dd>{sfrom}</dd>"
            f"<dt>Ships to</dt><dd>{sto}</dd>"
            f"<dt>Terms</dt><dd>{terms}</dd>"
            "</dl>"
            f"<p class=ref>Listing #{lid}</p></main>")
    return head("Listing") + body + FOOT


def vendor(handle, pgp, rating, joined, fbcount, feedback_dates):
    fb = "".join(f"<li class=fb><span class=fb-date>{d}</span> positive, smooth</li>"
                 for d in feedback_dates)
    return (head("Vendor") +
            f"<main><h1 class=vendor-handle>{handle}</h1>"
            "<table class=vendor-meta><tbody>"
            f"<tr><td>PGP</td><td class=v-pgp>{pgp}</td></tr>"
            f"<tr><td>Rating</td><td class=v-rating>{rating}</td></tr>"
            f"<tr><td>Joined</td><td class=v-joined>{joined}</td></tr>"
            f"<tr><td>Feedback</td><td class=v-feedback>{fbcount}</td></tr>"
            "</tbody></table>"
            f"<ul class=feedback>{fb}</ul></main>" + FOOT)


# ---- fixed identities (fake keys) ----
K_NIGHTHAWK = "9A3F1C4D7E20B5F8C6D1"
K_PAPERTRAIL = "2E77A0B9C31DFA45E9C2"
K_GREYOWL = "7C10FF93AB24EE6B1A80"
K_SALTMINE = "B4D2091AC7E63F5108AA"

pages = {}

# category index + category pages (with a honeypot link hidden in hardware)
pages["index.html"] = (head("Index") +
    "<main><h1>The Bazaar</h1><ul class=cats>"
    "<li><a href='/c/hardware'>Hardware</a></li>"
    "<li><a href='/c/digital'>Digital</a></li></ul></main>" + FOOT)

pages["category-hardware.html"] = (head("Hardware") +
    "<main><h1>Hardware</h1><ul class=listings>"
    "<li><a href='/l/1001'>sealed hardware wallet</a></li>"
    "<li><a href='/l/1002'>encrypted phone, wiped</a></li>"
    "<li><a href='/l/1005'>hardware wallet, sealed</a></li>"
    "<li><a href='/l/1006'>sealed hardware wallet</a></li>"
    "<a href='/trap/9f2a' class=hp style='display:none'>do not click</a>"
    "</ul></main>" + FOOT)

pages["category-digital.html"] = (head("Digital") +
    "<main><h1>Digital</h1><ul class=listings>"
    "<li><a href='/l/1003'>novelty ID template pack</a></li>"
    "<li><a href='/l/1004'>gift card codes, bulk</a></li>"
    "</ul></main>" + FOOT)

# listings 1001-1006
pages["listing-1001.html"] = listing(1001, "sealed hardware wallet", "NightHawk",
    "hardware", 180, "USD", "EU", "worldwide", "escrow, 2-of-3")
pages["listing-1002.html"] = listing(1002, "encrypted phone, wiped", "NightHawk",
    "hardware", 340, "USD", "EU", "EU", "escrow")
pages["listing-1003.html"] = listing(1003, "novelty ID template pack", "PaperTrail",
    "digital", 45, "USD", "n/a", "worldwide", "digital delivery, no refunds")
# drift variant of 1003 — same data, different markup
pages["listing-1003-v2.html"] = listing(1003, "novelty ID template pack", "PaperTrail",
    "digital", 45, "USD", "n/a", "worldwide", "digital delivery, no refunds", drift=True)
pages["listing-1004.html"] = listing(1004, "gift card codes, bulk", "GreyOwl",
    "digital", 90, "USD", "n/a", "worldwide", "instant, tiered")
# scam: bait price far below the ~180 median for wallets, "finalize early"
pages["listing-1005.html"] = listing(1005, "hardware wallet, sealed", "SaltMine",
    "hardware", 25, "USD", "EU", "worldwide", "finalize early, no escrow")
# resale ring: 1006 is 1001's listing reposted by a different vendor (Mimic)
pages["listing-1006.html"] = listing(1006, "sealed hardware wallet", "Mimic",
    "hardware", 180, "USD", "EU", "worldwide", "escrow, 2-of-3")

# vendors: 3 legit, 1 gamed-reputation, 1 borrowed-key
pages["vendor-nighthawk.html"] = vendor("NightHawk", K_NIGHTHAWK, "4.8",
    "2021-03", "342", ["2021-05-02", "2022-01-14", "2023-07-30", "2024-11-01", "2025-09-12"])
pages["vendor-papertrail.html"] = vendor("PaperTrail", K_PAPERTRAIL, "4.6",
    "2020-11", "518", ["2021-02-02", "2022-06-14", "2023-03-30", "2024-08-01", "2025-12-12"])
pages["vendor-greyowl.html"] = vendor("GreyOwl", K_GREYOWL, "4.9",
    "2019-06", "891", ["2020-01-02", "2021-06-14", "2022-03-30", "2023-08-01", "2025-05-12"])
# gamed: joined 2 weeks ago, 500 feedback, every entry the same week -> impossible velocity
pages["vendor-saltmine.html"] = vendor("SaltMine", K_SALTMINE, "5.0",
    "2026-07-25", "500", ["2026-07-25", "2026-07-25", "2026-07-26", "2026-07-26", "2026-07-27"])
# borrowed key: Mimic advertises NightHawk's PGP fingerprint (impersonation / key theft)
pages["vendor-mimic.html"] = vendor("Mimic", K_NIGHTHAWK, "4.2",
    "2026-06-30", "58", ["2026-07-01", "2026-07-08", "2026-07-15", "2026-07-20", "2026-07-28"])

# ---- defensive pages ----
pages["wall-captcha.html"] = (head("Checkpoint") +
    "<main><h1>Checkpoint</h1><form class=captcha action='/verify'>"
    "<p>Prove you are human to continue.</p>"
    "<img src='/captcha/challenge.png' alt='captcha challenge'>"
    "<input name='captcha_response' placeholder='enter the characters above'>"
    "<button>Verify</button></form></main>" + FOOT)

pages["wall-429.html"] = (head("Slow down") +
    "<main><h1>429 Too Many Requests</h1>"
    "<p>You are sending requests too quickly. Slow down and retry after 60 seconds.</p>"
    "</main>" + FOOT)

# poisoned catalogue: shaped like category-hardware but degraded/marked for a flagged account
pages["catalogue-poisoned.html"] = (head("Hardware") +
    "<main><h1>Hardware</h1>"
    "<div class=flag-notice>account under review — limited listings shown</div>"
    "<ul class=listings><li><a href='/l/0000'>placeholder</a></li></ul></main>" + FOOT)

# a byte-identical mirror of a category page, served from a second address —
# the store collapses it to one object (Chapter 10's exact-mirror case, at storage time)
pages["category-hardware-mirror.html"] = pages["category-hardware.html"]

here = os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(here, "corpus")
os.makedirs(outdir, exist_ok=True)
for name, html in pages.items():
    with open(os.path.join(outdir, name), "w") as fh:
        fh.write(html)
print(f"wrote {len(pages)} market-lab pages to {outdir}")
