#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Chapter 14 on real data: run the monitoring pipeline over the ransomwatch
leak-site feed (leaksite.db). The feed is a genuine change-feed — new victims
appear over time — so the same ideas from the synthetic labs (delta stream,
severity from bursts, correlation of cross-group events, dedup of reposts) show
up on real material.

Deterministic: reads the committed DB, prints a report, and --selftest asserts
stable properties. No network, no model.

Usage:  python3 monitor.py [--db leaksite.db] [--json] | --selftest
"""
import sqlite3, os, sys, json, statistics
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "leaksite.db")

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
    rows = c.execute("SELECT group_name, victim_id, ymd FROM posts ORDER BY ordinal").fetchall()

    # the change-feed as a weekly delta stream
    per_week = Counter()
    for g, v, ymd in rows:
        yr, mo, dy = map(int, ymd.split("-"))
        wk = f"{yr}-W{(__import__('datetime').date(yr, mo, dy).isocalendar()[1]):02d}"
        per_week[wk] += 1
    weekly = sorted(per_week.items())
    counts = [n for _, n in weekly]
    mean = statistics.mean(counts); sd = statistics.pstdev(counts)
    threshold = mean + 2 * sd
    bursts = [(w, n) for w, n in weekly if n > threshold]        # campaign spikes = severity

    # event taxonomy over the stream
    seen_victim = set(); seen_pair = set()
    n_new, n_repost, n_cross = 0, 0, 0
    victim_groups = defaultdict(set)
    for g, v, ymd in rows:
        if v not in seen_victim:
            n_new += 1; seen_victim.add(v)
        else:
            n_repost += 1
        if v in victim_groups and g not in victim_groups[v]:
            n_cross += 1
        victim_groups[v].add(g)

    # a concrete correlation candidate: one victim, two groups, days apart
    example = None
    for v, gs in victim_groups.items():
        if len(gs) > 1:
            hits = c.execute("SELECT group_name, ymd FROM posts WHERE victim_id=? ORDER BY ordinal", (v,)).fetchall()
            example = {"victim": v, "hits": hits}
            break

    return {
        "_snapshot": snapshot_line(db_path),
        "window": {"from": st["date_min"], "to": st["date_max"], "days": st["span_days"]},
        "posts": st["n_posts"], "groups": st["n_groups"], "victims": st["n_victims"],
        "weeks": len(weekly), "weekly_mean": round(mean, 1), "weekly_sd": round(sd, 1),
        "burst_threshold": round(threshold, 1), "bursts": bursts[:6], "n_bursts": len(bursts),
        "taxonomy": {"new_victim": n_new, "repost": n_repost, "cross_group": n_cross},
        "example": example,
        "top_groups": st["top_groups"][:5],
    }


def render(r):
    L = ["Chapter 14 monitoring over the real ransomwatch feed", ""]
    if r.get("_snapshot"):
        L += [r["_snapshot"], ""]
    w = r["window"]
    L.append(f'  feed window       {w["from"]} to {w["to"]}  ({w["days"]} days)')
    L.append(f'  volume            {r["posts"]} posts, {r["groups"]} groups, {r["victims"]} victims')
    L.append("")
    L.append(f'  change-feed        {r["weeks"]} weeks, mean {r["weekly_mean"]}/wk (sd {r["weekly_sd"]})')
    L.append(f'  severity: bursts   {r["n_bursts"]} weeks above {r["burst_threshold"]} new posts (campaign spikes)')
    for wk, n in r["bursts"]:
        L.append(f'    {wk}   {n} posts')
    L.append("")
    t = r["taxonomy"]
    L.append("  event taxonomy over the stream:")
    L.append(f'    new-victim   {t["new_victim"]}')
    L.append(f'    repost       {t["repost"]}   (dedup: same victim seen again)')
    L.append(f'    cross-group  {t["cross_group"]}   (correlate: same victim, another group)')
    if r["example"]:
        L.append("")
        L.append("  a real correlation candidate (one victim, two groups):")
        for g, ymd in r["example"]["hits"]:
            L.append(f'    {r["example"]["victim"]}  {g:16} {ymd}')
    L.append("")
    L.append(f'  most active groups: {", ".join(r["top_groups"])}')
    return "\n".join(L)


def selftest():
    r = analyze(DB)
    ok = (r["posts"] >= 5000 and r["groups"] >= 50
          and r["n_bursts"] >= 1
          and r["taxonomy"]["cross_group"] >= 1 and r["taxonomy"]["repost"] >= 1
          and r["example"] is not None and len(r["example"]["hits"]) >= 2)
    print(render(r)); print(); print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    db = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else DB
    r = analyze(db)
    print(json.dumps(r, indent=2) if "--json" in sys.argv else render(r))
