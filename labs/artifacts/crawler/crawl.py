#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""The crawler — Chapter 9 (Labs 9.1, 9.4, 9.5, 9.6, 9.7).

Ties the frontier, the fetch layer, and the extractor into one engine that starts
from seeds, holds a session past the login wall, follows links within the range's
scope, collapses mirrors by content hash, flags clones by structural match with
divergent key material, and emits one record per service in the exact format the
Chapter 8 scorer grades. The fetch layer is injected: the live lab passes a
Tor-SOCKS fetch, and --selftest passes an offline fixture and then runs the real
Chapter 8 scorer on the crawler's own output — closing the loop in the test itself.

The engine is parameterised (sessions / dedup / detect_clones) so a naive first
crawl (9.1) and the full engine (9.7) are the same code with features off vs on.
"""
import argparse
import json
import os
import sys
import time

from extract import content_hash, extract_keys, extract_links
from frontier import Frontier, host_of, normalize_url


def _structural(html, keys):
    """Hash of the page with its identity/payment material masked, so a clone
    (same layout, swapped pgp/btc) matches the original structurally."""
    masked = html
    if keys.get("pgp"):
        masked = masked.replace(keys["pgp"], "PGP")
    if keys.get("btc"):
        masked = masked.replace(keys["btc"], "BTC")
    return content_hash(masked)


def crawl(seeds, fetch, allow, min_delay=0.0, sessions=True, dedup=True, detect_clones=True):
    """Run the crawler; return a crawl-output dict {"discovered": [...]}.

    fetch(addr, session) -> (status, html, headers). One record is emitted per host
    (a service), keyed by its canonical http://host/ address."""
    fr = Frontier(allow=allow, min_delay=min_delay)
    fr.seed(seeds)
    session = {}
    services = {}   # host -> {address, chash, shash, keys}
    order = []

    while True:
        addr = fr.next()
        if addr is None:
            break
        wait = fr.wait_for(addr)
        if wait > 0:
            time.sleep(wait)            # politeness (0 in tests)
        status, html, headers = fetch(addr, session if sessions else None)
        fr.mark_fetched(addr)
        # login wall: authenticate once and retry the same path
        if status in (301, 302) and sessions and "login" in headers.get("location", ""):
            fetch(headers["location"], session)
            status, html, headers = fetch(addr, session)
        if status != 200 or not html:
            continue
        host = host_of(addr)
        if host not in services:
            keys = extract_keys(html)
            services[host] = {
                "address": normalize_url("http://" + host),
                "chash": content_hash(html),
                "shash": _structural(html, keys),
                "keys": keys,
            }
            order.append(host)
        for link, _net in extract_links(html, base=addr):
            fr.add(link)                 # scope guard filters off-range links

    discovered = []
    by_content = {}
    by_struct = {}
    for host in order:
        s = services[host]
        ch, sh, keys = s["chash"], s["shash"], s["keys"]
        if dedup and ch in by_content:
            discovered.append({"address": s["address"], "role": "mirror",
                               "same_as": by_content[ch]})
            continue
        if detect_clones and sh in by_struct and by_struct[sh][1] != keys:
            discovered.append({"address": s["address"], "role": "clone",
                               "flagged_clone": True})
            continue
        rec = {"address": s["address"], "role": "service"}
        if keys.get("pgp"):
            rec["pgp"] = keys["pgp"]
        if keys.get("btc"):
            rec["btc"] = keys["btc"]
        discovered.append(rec)
        by_content.setdefault(ch, s["address"])
        by_struct.setdefault(sh, (s["address"], keys))

    return {"discovered": discovered}


# ---- offline fixture: a miniature range, for --selftest ----------------------

def _fixture():
    names = ["dir", "mkt", "mir", "cln", "frm", "leak", "pst"]
    H = {n: chr(ord("a") + i) * 56 + ".onion" for i, n in enumerate(names)}
    U = {n: "http://" + H[n] + "/" for n in names}
    wm = "<div class=wm>SYNTHETIC</div>"
    market = (f"<html>{wm}<h1>Market</h1><p>pgp 9A3F1C4D7E20BQ btc bc1q_market_k7</p>"
              f"<a href='/listings'>catalogue</a></html>")
    clone = (f"<html>{wm}<h1>Market</h1><p>pgp 2E77A0B9C31DFP btc bc1q_clone_z9</p>"
             f"<a href='/listings'>catalogue</a></html>")
    content = {
        U["dir"]: (f"<html>{wm}<h1>Directory</h1>"
                   f"<a href='{U['mkt']}'>market</a><a href='{U['frm']}'>forum</a>"
                   f"<a href='{U['mir']}'>market mirror</a></html>"),   # leak/paste/clone absent
        U["mkt"]: market,
        U["mir"]: market,                                              # identical -> mirror
        U["cln"]: clone,                                               # swapped keys -> clone
        U["frm"]: f"<html>{wm}<h1>Forum</h1><p>deal here {U['cln']}</p></html>",  # phishing link
        U["leak"]: f"<html>{wm}<h1>Leak</h1><p>no real breach data</p></html>",   # unlinked
        U["pst"]: f"<html>{wm}<h1>Paste</h1></html>",
    }
    listings = U["mkt"] + "listings"
    listings_html = f"<html>{wm}<h1>Listings</h1><a href='{U['pst']}'>paste</a></html>"

    def fetch(addr, session):
        if addr == listings:
            if session and session.get("auth"):
                return 200, listings_html, {}
            return 302, "", {"location": U["mkt"] + "login"}
        if addr == U["mkt"] + "login":
            if session is not None:
                session["auth"] = True
            return 200, f"<html>{wm}ok</html>", {}
        if addr in content:
            return 200, content[addr], {}
        return 404, "", {}

    manifest = {
        "logical_services": ["directory", "market", "forum", "leak", "paste"],
        "addresses": {
            U["dir"]:  {"service": "directory"},
            U["mkt"]:  {"service": "market", "pgp": "9A3F1C4D7E20BQ", "btc": "bc1q_market_k7"},
            U["frm"]:  {"service": "forum"},
            U["leak"]: {"service": "leak"},
            U["pst"]:  {"service": "paste"},
            U["mir"]:  {"service": "market", "mirror": True},
            U["cln"]:  {"service": "market", "clone": True, "altered": ["pgp", "btc"],
                        "genuine_pgp": "9A3F1C4D7E20BQ", "genuine_btc": "bc1q_market_k7",
                        "clone_pgp": "2E77A0B9C31DFP", "clone_btc": "bc1q_clone_z9"},
        },
    }
    allow = {H[n] for n in names}      # scope = every range host (from ./lab range list)
    return U["dir"], fetch, allow, manifest


def selftest():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "range-scorer"))
    import scorer

    seed, fetch, allow, manifest = _fixture()
    naive = scorer.score(manifest, crawl([seed], fetch, allow,
                                         sessions=False, dedup=False, detect_clones=False))
    full = scorer.score(manifest, crawl([seed], fetch, allow,
                                        sessions=True, dedup=True, detect_clones=True))

    ok = True
    # naive: no session (misses paste), no dedup (mirror uncollapsed), clone believed
    if not (naive["recall"] == 0.6 and naive["mirrors_collapsed"] == 0
            and naive["clones_caught"] == 0 and naive["clones_believed"]
            and naive["clones_believed"][0]["trusted_swapped_payment"] is True):
        ok = False
    # full: session finds paste (recall up), mirror collapsed, clone caught, precision 1.0
    if not (full["recall"] == 0.8 and full["missed"] == ["leak"]
            and full["precision"] == 1.0
            and full["mirrors_collapsed"] == 1
            and full["clones_caught"] == 1 and not full["clones_believed"]):
        ok = False
    # the engine strictly improves on every axis
    if not (full["recall"] > naive["recall"] and full["precision"] >= naive["precision"]
            and full["mirrors_collapsed"] > naive["mirrors_collapsed"]
            and full["clones_caught"] > naive["clones_caught"]):
        ok = False

    print(f"selftest: naive crawl scores recall {naive['recall']:.2f}, mirror 0/1, clone believed;")
    print(f"          full engine scores recall {full['recall']:.2f}, precision "
          f"{full['precision']:.2f}, mirror 1/1, clone caught  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", help="(lab use) write crawl-output.json — requires a live fetch layer")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest (a live crawl runs via ./lab crawl range)")
