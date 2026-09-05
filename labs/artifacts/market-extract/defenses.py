#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Anti-crawling countermeasures — detect, never defeat — Chapter 11 (Lab 11.3).

A market fights collection, and a research crawler answers within the rules. This
module recognises the four things a market throws back and routes each to the correct
restrained response: a CAPTCHA wall is queued for a human to solve manually and the
crawler stops on that path — it is NEVER solved automatically, and there is no solver
in this file to call; a rate-limit response triggers a backoff; a honeypot link (one a
human could never see or would be told not to click) is skipped so following it cannot
flag the account; and a poisoned catalogue served to a flagged account is detected and
refused rather than extracted as if it were real. The guarantee is structural: the only
verbs here are detect, queue, back off, and skip. Solving a wall is out of scope by
construction, the same way the Chapter 9 scope guard is not configurable to reach the
real dark web.
"""
import argparse
import glob
import os
import re
import sys

_TAG = re.compile(r"<[^>]+>")


def _text(html):
    return re.sub(r"\s+", " ", _TAG.sub(" ", html)).strip().lower()


def is_captcha(html):
    t = _text(html)
    if re.search(r"class=['\"]?captcha", html, re.I):
        return True
    return ("prove you are human" in t or "verify you are human" in t
            or "captcha_response" in html.lower())


def is_rate_limited(html, status=200):
    if status == 429:
        return True
    t = _text(html)
    return ("too many requests" in t or "slow down" in t or "retry after" in t)


def is_poisoned(html):
    """Shadow-ban tell: a catalogue that announces the account is restricted/flagged."""
    t = _text(html)
    return ("under review" in t or "account has been flagged" in t
            or "limited listings shown" in t or re.search(r"class=['\"]?flag-notice", html, re.I) is not None)


def honeypot_links(html):
    """Links a human would never follow — hidden by CSS, marked do-not-click, or trapped."""
    out = []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", html, re.I | re.S):
        attrs, text = m.group(1), _text(m.group(2))
        href = re.search(r'href=["\']([^"\']+)', attrs)
        hidden = ("display:none" in attrs.replace(" ", "").lower()
                  or "visibility:hidden" in attrs.replace(" ", "").lower()
                  or re.search(r'class=["\']?hp', attrs, re.I))
        if href and (hidden or "do not click" in text):
            out.append(href.group(1))
    return out


# the response policy — detect and restrain, never defeat
_POLICY = {"captcha": "queue", "rate_limited": "backoff", "poisoned": "skip", "ok": "proceed"}


def classify(html, status=200):
    """Return the kind of response and the restrained action to take.
    A CAPTCHA is only ever queued for a human — it is never solved here."""
    if is_rate_limited(html, status):
        kind = "rate_limited"
    elif is_captcha(html):
        kind = "captcha"
    elif is_poisoned(html):
        kind = "poisoned"
    else:
        kind = "ok"
    return {"kind": kind, "action": _POLICY[kind]}


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    C = {os.path.basename(p): open(p).read()
         for p in glob.glob(os.path.join(here, "corpus", "*.html"))}
    ok = True

    cap = classify(C["wall-captcha.html"])
    if not (cap["kind"] == "captcha" and cap["action"] == "queue"):
        print(f"  captcha -> {cap}")
        ok = False
    rl = classify(C["wall-429.html"], status=429)
    if not (rl["kind"] == "rate_limited" and rl["action"] == "backoff"):
        ok = False
    poi = classify(C["catalogue-poisoned.html"])
    if not (poi["kind"] == "poisoned" and poi["action"] == "skip"):
        print(f"  poisoned -> {poi}")
        ok = False
    good = classify(C["listing-1001.html"])
    if not (good["kind"] == "ok" and good["action"] == "proceed"):
        ok = False

    # the honeypot link in the hardware category is detected and would be skipped
    hp = honeypot_links(C["category-hardware.html"])
    if not (len(hp) == 1 and "/trap/" in hp[0]):
        print(f"  honeypot -> {hp}")
        ok = False

    # structural guarantee: a CAPTCHA is only ever queued, and no solver exists here
    if classify(C["wall-captcha.html"])["action"] != "queue":
        ok = False
    if "solve_captcha" in globals() or "solve" in globals():
        print("  a solver must not exist in this module")
        ok = False

    print("selftest: CAPTCHA is queued for a human (never solved), rate limits back off,")
    print(f"          honeypots are skipped, poisoned catalogues refused  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan", metavar="DIR")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.scan:
        for name in ["wall-captcha.html", "wall-429.html", "catalogue-poisoned.html"]:
            status = 429 if "429" in name else 200
            c = classify(open(os.path.join(a.scan, name)).read(), status)
            print(f"  {name:28} -> {c['kind']:12} action: {c['action']}")
        hp = honeypot_links(open(os.path.join(a.scan, "category-hardware.html")).read())
        print(f"  honeypot links detected: {hp} (skipped)")
        print("  CAPTCHA is queued for a human — never solved (no solver in this module)")
        sys.exit(0)
    ap.error("use --selftest or --scan DIR")
