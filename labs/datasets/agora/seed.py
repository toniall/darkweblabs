#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Build market.db from a public Agora darknet-market dataset (market dead since
2015). Feeds Chapter 11, offline: real vendor-graph topology, real price tiers,
real shipping lanes, and real feedback quality, used to (a) calibrate the
synthetic market's distributions and (b) drive an optional real-slice extraction
lab.

SCOPE NOTE: this particular public dataset is cannabis-focused (every category is
a cannabis subtype), so the real-slice lab is a *cannabis-market slice*, honestly
labelled. The graded synthetic market stays diverse; it only borrows the shapes
(vendor concentration, price tiers, lane mix, feedback ratios) from here.

Scrubbing: vendor names -> stable salted pseudonyms (vendor-XXXX), so the vendor
graph keeps its shape without naming anyone. Product and feedback FREE-TEXT is
dropped entirely; only category / price-tier / lane / rating structure is kept.

Usage:
  python3 seed.py [--src DIR] [--out market.db] [--cap N] [--selftest]

Source repo layout: DIR/data/arules/Ag2014-ssc*.csv
"""
import sqlite3, csv, re, sys, os, hashlib, glob, statistics
from collections import Counter, defaultdict

SALT = "darkweblabs-agora-v1"
csv.field_size_limit(10_000_000)


def pseudonym(name):
    h = hashlib.sha256((SALT + "|" + name.strip().lower()).encode()).hexdigest()
    return "vendor-" + h[:5]


def clean_place(s):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    if not s or s.lower() in ("na", "n/a", "none", "-"):
        return "Unknown"
    if s.lower() in ("usa", "eu", "uk", "us"):
        return s.upper()
    return s.title()


def parse_price(p):
    nums = re.findall(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", (p or "").lower())
    if len(nums) >= 2:
        try:
            return float(nums[0]), float(nums[1])
        except ValueError:
            return None, None
    return None, None


def rating_class(row):
    if row.get("goodFB") == "TRUE" or row.get("greatFB") == "TRUE":
        return "pos"
    if row.get("poorFB") == "TRUE" or row.get("badFB") == "TRUE" or row.get("worstFB") == "TRUE":
        return "neg"
    return "neu"


def load(src, cap):
    files = sorted(glob.glob(os.path.join(src, "data", "arules", "Ag2014-ssc*.csv")))
    listings = {}          # list_id -> record (distinct listing)
    fb = defaultdict(lambda: Counter())   # list_id -> {pos,neu,neg}
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                lid = (row.get("list") or "").strip()
                if not lid:
                    continue
                fb[lid][rating_class(row)] += 1
                if lid not in listings:
                    lo, hi = parse_price(row.get("price"))
                    listings[lid] = {
                        "date": (row.get("date") or "").strip(),
                        "vendor": pseudonym(row.get("vendor") or "unknown"),
                        "cat": (row.get("cat") or "").strip(),
                        "subcat": (row.get("subcat") or "").strip(),
                        "subsubcat": (row.get("subsubcat") or "").strip(),
                        "plo": lo, "phi": hi,
                        "origin": clean_place(row.get("from")),
                        "dest": clean_place(row.get("to")),
                    }
    items = list(listings.items())
    if cap and len(items) > cap:
        items = sorted(items)[:cap]           # deterministic slice
    return items, fb


def build(src, out, cap):
    if os.path.exists(out):
        os.remove(out)
    items, fb = load(src, cap)
    db = sqlite3.connect(out)
    c = db.cursor()
    c.executescript("""
      CREATE TABLE listings(
        list_id TEXT PRIMARY KEY, date TEXT, vendor_id TEXT,
        category TEXT, subcategory TEXT, subsubcategory TEXT,
        price_btc_low REAL, price_btc_high REAL, origin TEXT, dest TEXT,
        n_feedback INT, fb_pos INT, fb_neg INT);
      CREATE TABLE vendors(
        vendor_id TEXT PRIMARY KEY, n_listings INT, n_subcategories INT,
        origins TEXT, first_date TEXT, last_date TEXT,
        total_feedback INT, positive_rate REAL);
      CREATE TABLE stats(key TEXT PRIMARY KEY, value TEXT);
      CREATE INDEX ix_listings_vendor ON listings(vendor_id);
    """)
    import json
    by_v = defaultdict(list)
    lanes = Counter(); tiers = Counter(); subcats = Counter(); ratings = Counter()
    for lid, r in items:
        counts = fb[lid]
        npos, nneg, nneu = counts["pos"], counts["neg"], counts["neu"]
        ntot = npos + nneg + nneu
        c.execute("INSERT INTO listings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (lid, r["date"], r["vendor"], r["cat"], r["subcat"], r["subsubcat"],
                   r["plo"], r["phi"], r["origin"], r["dest"], ntot, npos, nneg))
        by_v[r["vendor"]].append((r, ntot, npos))
        lanes[f'{r["origin"]}->{r["dest"]}'] += 1
        if r["plo"] is not None:
            tiers[f'[{r["plo"]:.2g},{r["phi"]:.2g})'] += 1
        subcats[r["subsubcat"] or r["subcat"]] += 1
        ratings["pos"] += npos; ratings["neg"] += nneg; ratings["neu"] += nneu

    for v, rows in by_v.items():
        dates = [x[0]["date"] for x in rows if x[0]["date"]]
        tot_fb = sum(x[1] for x in rows); pos_fb = sum(x[2] for x in rows)
        c.execute("INSERT INTO vendors VALUES(?,?,?,?,?,?,?,?)",
                  (v, len(rows), len({x[0]["subsubcat"] for x in rows}),
                   json.dumps(sorted({x[0]["origin"] for x in rows if x[0]["origin"]})[:6]),
                   min(dates) if dates else "", max(dates) if dates else "",
                   tot_fb, round(pos_fb / tot_fb, 4) if tot_fb else 0.0))

    # derived distributions for the calibrated-synthetic market
    vcounts = sorted((len(r) for r in by_v.values()), reverse=True)
    total_listings = len(items)
    top10 = sum(vcounts[:10])
    stats = {
        "n_listings": total_listings,
        "n_vendors": len(by_v),
        "listings_per_vendor_median": int(statistics.median(vcounts)) if vcounts else 0,
        "listings_per_vendor_max": vcounts[0] if vcounts else 0,
        "top10_vendor_share": round(top10 / total_listings, 4) if total_listings else 0,
        "top_lanes": [l for l, _ in lanes.most_common(8)],
        "price_tiers": dict(tiers.most_common(8)),
        "subcategory_mix": dict(subcats.most_common(10)),
        "feedback_positive_rate": round(ratings["pos"] / max(sum(ratings.values()), 1), 4),
        "dataset": "Agora cannabis-market slice (2014-2015, dead market)",
    }
    for k, v in stats.items():
        c.execute("INSERT INTO stats VALUES(?,?)", (k, json.dumps(v)))
    import datetime as _dt   # provenance + freshness stamp (dead archive: date reflects the rebuild)
    c.execute("INSERT OR REPLACE INTO stats VALUES(?,?)", ("captured_at", json.dumps(_dt.date.today().isoformat())))
    c.execute("INSERT OR REPLACE INTO stats VALUES(?,?)", ("source", json.dumps("https://github.com/mozzarellaV8/agora-marketplace.git")))
    db.commit()
    return db


def selftest(out):
    import json
    db = sqlite3.connect(out); c = db.cursor()
    nl = c.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    nv = c.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
    bad = c.execute("SELECT COUNT(*) FROM listings WHERE vendor_id NOT LIKE 'vendor-%'").fetchone()[0]
    share = json.loads(c.execute("SELECT value FROM stats WHERE key='top10_vendor_share'").fetchone()[0])
    lanes = json.loads(c.execute("SELECT value FROM stats WHERE key='top_lanes'").fetchone()[0])
    ok = nl >= 1000 and nv >= 50 and bad == 0 and 0 < share <= 1 and len(lanes) > 0
    print(f"listings={nl} vendors={nv} pseudonym-leaks={bad} top10-share={share} lanes={len(lanes)}")
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    import subprocess, tempfile
    args = sys.argv[1:]
    here = os.path.dirname(os.path.abspath(__file__))
    out = args[args.index("--out") + 1] if "--out" in args else os.path.join(here, "market.db")
    cap = int(args[args.index("--cap") + 1]) if "--cap" in args else 12000
    if "--selftest" in args and "--src" not in args:
        sys.exit(selftest(out))
    src = args[args.index("--src") + 1] if "--src" in args else None
    cleanup = False
    if not src:
        src = tempfile.mkdtemp(prefix="agora-")
        subprocess.run(["git", "clone", "--depth", "1", "--quiet",
                        "https://github.com/mozzarellaV8/agora-marketplace.git", src], check=True)
        cleanup = True
    print(f"building {out} from {src} (cap {cap}) ...")
    build(src, out, cap)
    if cleanup:
        subprocess.run(["rm", "-rf", src])
    sys.exit(selftest(out))
