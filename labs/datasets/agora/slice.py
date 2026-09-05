#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Chapter 11 on real data: run market extraction and the vendor graph over a
scrubbed slice of the Agora market (market.db). Structured listings, vendor
concentration, shipping lanes, price tiers, and feedback quality are all real
(cannabis-market slice, dead since 2015). These distributions are what calibrate
the diverse synthetic market used in the graded labs.

Deterministic. Usage:  python3 slice.py [--db market.db] [--json] | --selftest
"""
import sqlite3, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "market.db")

def snapshot_line(db_path):
    """Data-provenance banner: source, capture date, and how current the feed is.
    These come from the bundled snapshot; ./lab update re-fetches and re-stamps them."""
    try:
        c = sqlite3.connect(db_path)
        st = {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}
        c.close()
    except Exception:
        st = {}
    src = (st.get("source", "") or "").rstrip("/").replace("https://github.com/", "").replace(".git", "") or "bundled snapshot"
    cap = st.get("captured_at", "unknown")
    through = st.get("date_max")
    tail = ", posts through %s" % through if through else ""
    return "  data snapshot     %s \u00b7 captured %s%s  (run ./lab update to refresh)" % (src, cap, tail)



def analyze(db_path):
    c = sqlite3.connect(db_path).cursor()
    st = {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}

    top_vendors = c.execute(
        "SELECT vendor_id, n_listings, n_subcategories, positive_rate FROM vendors ORDER BY n_listings DESC LIMIT 6").fetchall()
    # vendor-graph edges: vendor -> distinct shipping lanes (origins)
    multi_origin = c.execute("""SELECT vendor_id, COUNT(DISTINCT origin) o FROM listings
                                WHERE origin != '' GROUP BY vendor_id HAVING o > 1 ORDER BY o DESC LIMIT 1""").fetchone()
    with_fb = c.execute("SELECT COUNT(*) FROM listings WHERE n_feedback > 0").fetchone()[0]
    total = st["n_listings"]

    return {
        "_snapshot": snapshot_line(db_path),
        "listings": total, "vendors": st["n_vendors"],
        "with_feedback": with_fb,
        "listings_per_vendor_median": st["listings_per_vendor_median"],
        "listings_per_vendor_max": st["listings_per_vendor_max"],
        "top10_vendor_share": st["top10_vendor_share"],
        "feedback_positive_rate": st["feedback_positive_rate"],
        "top_lanes": st["top_lanes"][:5],
        "price_tiers": st["price_tiers"],
        "subcategory_mix": st["subcategory_mix"],
        "top_vendors": top_vendors,
        "multi_origin_vendor": multi_origin,
        "dataset": st["dataset"],
    }


def render(r):
    L = ["Chapter 11 market extraction + vendor graph over a real Agora slice", ""]
    if r.get("_snapshot"):
        L += [r["_snapshot"], ""]
    L.append(f'  dataset           {r["dataset"]}')
    L.append(f'  extracted         {r["listings"]} listings, {r["vendors"]} vendors ({r["with_feedback"]} with feedback)')
    L.append("")
    L.append("  vendor graph, biggest nodes:")
    for v in r["top_vendors"]:
        L.append(f'    {v[0]:12} {v[1]:4} listings  {v[2]} subcats  {int(v[3]*100)}% positive')
    if r["multi_origin_vendor"]:
        L.append(f'    multi-lane vendor: {r["multi_origin_vendor"][0]} ships from {r["multi_origin_vendor"][1]} origins')
    L.append("")
    L.append("  real distributions that calibrate the synthetic market:")
    L.append(f'    vendor concentration   top-10 vendors = {int(r["top10_vendor_share"]*100)}% of listings')
    L.append(f'    listings per vendor    median {r["listings_per_vendor_median"]}, max {r["listings_per_vendor_max"]}')
    L.append(f'    feedback positive rate {int(r["feedback_positive_rate"]*100)}%')
    L.append(f'    top shipping lanes     {", ".join(r["top_lanes"])}')
    L.append(f'    price tiers (BTC)      {", ".join(list(r["price_tiers"].keys())[:4])}')
    return "\n".join(L)


def selftest():
    r = analyze(DB)
    ok = (r["listings"] >= 1000 and r["vendors"] >= 50
          and 0 < r["top10_vendor_share"] <= 1
          and 0 < r["feedback_positive_rate"] <= 1
          and len(r["top_lanes"]) >= 1 and len(r["top_vendors"]) >= 3)
    print(render(r)); print(); print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    db = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else DB
    r = analyze(db)
    print(json.dumps(r, indent=2) if "--json" in sys.argv else render(r))
