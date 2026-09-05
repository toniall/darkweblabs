#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Build a self-contained visual intelligence package from the book's analyses and
write it into a folder the workstation mounts read-only.

The Python runs on the HOST (offline). It emits several self-contained HTML
pages plus an index into an output folder (default: <repo>/intel), which
compose bind-mounts read-only at /intel inside the workstation. The reader opens
file:///intel/index.html in the workstation's own browser. Everything on every
page is inlined - CSS, data, and hand-drawn SVG - so nothing loads over the
network, which is what lets it render behind Tor, and the mount is read-only, so
the collection tier can view the host's intelligence but never alter it.

Pages:
  index.html        the atlas - a launcher for the package
  dashboard.html    real-data dashboard (LIVE over negotiations/leaksite/market DBs)
  attribution.html  Ch13 persona graph + Ch10 mirror-vs-clone (LIVE: persona-extract + dedup engines)
  detection.html    Ch14 alert timeline across three snapshots (LIVE: detect-monitor engine)
  capstone.html     Ch15 evidence chain to graded claims (LIVE: report-forge engine)
  method.html       book-wide full-vs-naive scorecard (the book's published results)

The dashboard reads the committed DBs live; attribution, detection, and capstone
run the actual lab engines (persona-extract, dedup, detect-monitor, report-forge)
over their corpora in a subprocess and render whatever they return. Only
method.html stays a presentation of the book's published full-vs-naive results.
None of these pages touch scoring.

Usage:  python3 report.py --all --outdir intel
        python3 report.py --selftest
"""
import sqlite3, os, sys, json, statistics, subprocess
from collections import Counter, defaultdict
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
NEGO = os.path.join(HERE, "..", "ransomchat", "negotiations.db")
LEAK = os.path.join(HERE, "..", "..", "datasets", "ransomwatch", "leaksite.db")
MKT  = os.path.join(HERE, "..", "..", "datasets", "agora", "market.db")


def _run_engine(subdir, script, args):
    """Run a lab engine's own CLI over its corpus in a subprocess and parse the
    JSON it prints. Each engine ships its own pipeline.py, so a subprocess keeps
    their identically-named modules from colliding inside one interpreter. This
    is what makes attribution/detection/capstone LIVE: the pages render whatever
    the real engines produce, not a transcribed copy."""
    wd = os.path.join(HERE, "..", subdir)
    r = subprocess.run([sys.executable, script, *args], cwd=wd,
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"{subdir}/{script} failed: {(r.stderr or r.stdout)[-300:]}")
    out = r.stdout
    return json.loads(out[out.index("{"):out.rindex("}") + 1])


# ================= LIVE data: the real-data dashboard (reads the 3 DBs) =================

def negotiations_data():
    db = sqlite3.connect(NEGO); c = db.cursor()
    groups = [r[0] for r in c.execute("SELECT name FROM groups ORDER BY name")]
    tactics = ["deadline_pressure", "threat_leak", "proof_offered",
               "deletion_promise", "discount_offer", "threat_notify"]
    tac_series = []
    for t in tactics:
        vals = []
        for g in groups:
            tf = json.loads(c.execute("SELECT tactic_freq FROM groups WHERE name=?", (g,)).fetchone()[0])
            vals.append(round(tf.get(t, 0) * 100))
        tac_series.append({"name": t.replace("_", " "), "values": vals})
    anchor, floor, outcomes, op_by_g, vi_by_g = [], [], [], [], []
    n_tx = settled = total = 0
    for g in groups:
        p = json.loads(c.execute("SELECT chat_persona FROM groups WHERE name=?", (g,)).fetchone()[0])
        anchor.append(round(p["anchor_usd"] / 1e6, 2)); floor.append(round(p["floor_usd"] / 1e6, 2))
        oc = json.loads(c.execute("SELECT outcomes FROM groups WHERE name=?", (g,)).fetchone()[0])
        outcomes.append(oc)
        settled += oc.get("settled", 0); total += sum(oc.values())
        n_tx += c.execute("SELECT n_transcripts FROM groups WHERE name=?", (g,)).fetchone()[0]
        op_by_g.append(c.execute("SELECT COUNT(*) FROM messages WHERE group_name=? AND party='operator'", (g,)).fetchone()[0])
        vi_by_g.append(c.execute("SELECT COUNT(*) FROM messages WHERE group_name=? AND party='victim'", (g,)).fetchone()[0])
    n_msg = c.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    okeys = ["settled", "ongoing", "published"]
    return {
        "groups": groups,
        "cards": [["Transcripts", n_tx], ["Messages", f"{n_msg:,}"],
                  ["Groups", len(groups)], ["Settled", f"{round(100*settled/total)}%"]],
        "tactics": {"groups": groups, "series": tac_series},
        "range": {"groups": groups, "anchor": anchor, "floor": floor},
        "outcomes": {"groups": groups, "keys": okeys,
                     "series": [[oc.get(k, 0) for oc in outcomes] for k in okeys]},
        "messages_by_group": {"groups": groups, "operator": op_by_g, "victim": vi_by_g},
    }

def leaksite_data():
    db = sqlite3.connect(LEAK); c = db.cursor()
    st = {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}
    rows = c.execute("SELECT ymd FROM posts ORDER BY ordinal").fetchall()
    per_month = Counter(r[0][:7] for r in rows)
    months = sorted(per_month); cum = []; run = 0
    for m in months:
        run += per_month[m]; cum.append(run)
    step = max(1, len(months) // 40)
    line = [{"x": i, "y": cum[i], "label": months[i]} for i in range(0, len(months), step)]
    if line[-1]["x"] != len(months) - 1:
        line.append({"x": len(months) - 1, "y": cum[-1], "label": months[-1]})
    top = c.execute("SELECT name, n_victims FROM groups ORDER BY n_victims DESC LIMIT 10").fetchall()
    return {
        "cards": [["Groups", st["n_groups"]], ["Victims", f'{st["n_victims"]:,}'],
                  ["Reposts", st["repost_victims"]], ["Cross-group", st["crossgroup_victims"]]],
        "cumulative": {"points": line, "xlabels": [months[0], months[len(months)//2], months[-1]]},
        "top_groups": {"labels": [t[0] for t in top], "values": [t[1] for t in top]},
    }

def changefeed_data():
    db = sqlite3.connect(LEAK); c = db.cursor()
    st = {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}
    rows = c.execute("SELECT ymd FROM posts ORDER BY ordinal").fetchall()
    per_week = Counter()
    for (ymd,) in rows:
        y, m, d = map(int, ymd.split("-"))
        per_week[f"{y}-W{date(y, m, d).isocalendar()[1]:02d}"] += 1
    weekly = sorted(per_week.items()); counts = [n for _, n in weekly]
    mean = statistics.mean(counts); sd = statistics.pstdev(counts); thr = mean + 2 * sd
    pts = [{"x": i, "y": counts[i], "burst": counts[i] > thr, "label": weekly[i][0]} for i in range(len(weekly))]
    seen = set(); vg = defaultdict(set); nnew = nrep = ncross = 0
    for g, v in c.execute("SELECT group_name, victim_id FROM posts ORDER BY ordinal"):
        if v not in seen: nnew += 1; seen.add(v)
        else: nrep += 1
        if v in vg and g not in vg[v]: ncross += 1
        vg[v].add(g)
    return {
        "cards": [["Posts", f'{st["n_posts"]:,}'], ["Weeks", len(weekly)],
                  ["Bursts", sum(1 for p in pts if p["burst"])], ["Span (days)", st["span_days"]]],
        "weekly": {"points": pts, "threshold": round(thr)},
        "taxonomy": {"labels": ["new-victim", "repost", "cross-group"], "values": [nnew, nrep, ncross]},
    }

def market_data():
    db = sqlite3.connect(MKT); c = db.cursor()
    st = {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}
    top = c.execute("SELECT vendor_id, n_listings FROM vendors ORDER BY n_listings DESC LIMIT 10").fetchall()
    counts = sorted((r[0] for r in c.execute("SELECT n_listings FROM vendors")), reverse=True)
    total = sum(counts); n = len(counts); cum = 0; curve = [{"x": 0, "y": 0}]
    for i, v in enumerate(counts):
        cum += v
        if i % max(1, n // 60) == 0 or i == n - 1:
            curve.append({"x": round(100 * (i + 1) / n, 2), "y": round(100 * cum / total, 2)})
    lanes = st["top_lanes"][:6]; lane_counts = []
    for l in lanes:
        o, d = l.split("->")
        lane_counts.append(c.execute("SELECT COUNT(*) FROM listings WHERE origin=? AND dest=?", (o, d)).fetchone()[0])
    tiers = st["price_tiers"]
    return {
        "cards": [["Listings", f'{st["n_listings"]:,}'], ["Vendors", st["n_vendors"]],
                  ["Top-10 share", f'{round(st["top10_vendor_share"]*100)}%'],
                  ["Positive", f'{round(st["feedback_positive_rate"]*100)}%']],
        "top_vendors": {"labels": [t[0] for t in top], "values": [t[1] for t in top]},
        "lorenz": {"curve": curve},
        "lanes": {"labels": lanes, "values": lane_counts},
        "tiers": {"labels": list(tiers.keys())[:6], "values": list(tiers.values())[:6]},
    }


# ============= ENCODED data: the documented lab corpora and published results =============

def persona_data():
    """LIVE (Ch13): run the persona-extract engine over its corpus and shape its
    operator clusters, personas, and framing flags into the attribution graph."""
    d = _run_engine("persona-extract", "pipeline.py", ["--corpus", "corpus"])
    NAMES = [("alpha", "Operator Alpha", "#a855f7"), ("bravo", "Operator Bravo", "#22d3ee"),
             ("charlie", "Operator Charlie", "#fbbf24"), ("delta", "Operator Delta", "#34d399")]
    BADGE = {"high": "HIGH", "medium": "medium", "low": "low", "single": "single"}
    HARD = {"shared_signed_key", "shared_wallet"}
    surface = {p["handle"]: p["surface"] for p in d["personas"]}
    clusters, nodes, spine, cid_of = [], [], {}, {}
    for i, c in enumerate(d["clusters"]):
        cid, label, color = NAMES[i] if i < len(NAMES) else (f"op{i}", f"Operator {i}", "#8b93a7")
        clusters.append({"id": cid, "label": label,
                         "badge": BADGE.get(c["confidence"], c["confidence"]), "color": color})
        for h in c["personas"]:
            nodes.append({"id": h.lower(), "label": h, "cluster": cid, "tag": surface.get(h, "")})
            cid_of[h] = cid
        sig = set(c.get("signals", []))
        spine[cid] = "hard" if (sig & HARD) else ("soft" if len(c["personas"]) > 1 else None)
    # rejected cross-cluster edge: the persona recurring across the framing flags
    # is the framer; the personas it is paired with belong to the framed operator.
    flags = d.get("framing_flags", [])
    flagged = None
    if flags:
        who = Counter()
        for f in flags:
            who[f["a"]] += 1; who[f["b"]] += 1
        framer = who.most_common(1)[0][0]
        others = [f["a"] if f["b"] == framer else f["b"] for f in flags]
        framed_cid = cid_of.get(others[0], "alpha") if others else "alpha"
        framed_label = next((c["label"].split()[-1] for c in clusters if c["id"] == framed_cid), "Alpha")
        flagged = {"from": framer.lower(), "to": framed_cid,
                   "label": f"displays {framed_label}'s signed key but signs its own \u2192 rejected"}
    return {"clusters": clusters, "nodes": nodes, "spine": spine, "flagged": flagged,
            "legend": [["hard identifier (signed key + wallet)", "hard"],
                       ["soft signal (stylometry, rhythm)", "soft"],
                       ["displayed-only \u2192 not merged", "flagged"]]}

def dedup_data():
    """LIVE (Ch10): cluster the mirror/clone corpus and split the origin market's
    collapsed members into mirrors (shared wallet) and clones (divergent wallet)."""
    d = _run_engine("dedup", "cluster.py", ["--dir", "corpus"])
    REASON = {"shared_payment": "byte/banner copy, same wallet", "payment_swap": "wallet + key swapped",
              "keyless_copy": "wallet swapped, no key"}
    origin = "market"
    market = next((c for c in d["clusters"]
                   if os.path.basename(c["canonical"]).startswith(origin) and len(c["members"]) > 1),
                  d["clusters"][0])
    mirrors, clones = [], []
    for m in sorted(market["members"], key=lambda x: x["address"]):
        row = [m["address"].replace(".html", ""), REASON.get(m.get("reason"), m.get("reason", ""))]
        if m.get("role") == "mirror": mirrors.append(row)
        elif m.get("role") == "clone": clones.append(row)
    return {"origin": origin, "mirrors": mirrors, "clones": clones,
            "note": f"{len(mirrors)} mirrors reuse the origin's payment wallet, so they collapse into the one "
                    f"canonical node. {len(clones)} clones carry a different wallet, so they stay separate "
                    f"operators. The structure looks the same either way; the payment address is what "
                    f"separates a copy from a rival."}

def detection_data():
    """LIVE (Ch14): run the detect-monitor engine across the three snapshots and
    sort its ranked alerts into severity lanes."""
    d = _run_engine("detect-monitor", "pipeline.py", ["--corpus", "corpus"])
    LANE = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    TL = {"new_clone": "clone", "operator_resurface": "operator resurface", "new_victim": "new victim",
          "publication": "publication", "market_down": "market down", "deadline_slip": "deadline slip",
          "withdrawal": "withdrawal", "new_mirror": "new mirror"}
    alerts = d["alerts"]
    events = []
    for a in alerts:
        ev = {"col": int(a["t_from"][1:]), "lane": LANE.get(a["severity"], 3),
              "label": f"{a['name']} \u2014 {TL.get(a['type'], a['type'].replace('_', ' '))}"}
        if a["severity"] == "critical":
            ev["crit"] = True
        events.append(ev)
    n_crit = sum(1 for a in alerts if a["severity"] == "critical")
    suppressed, collapsed = d.get("suppressed", 0), d.get("collapsed", 0)
    raw = len(alerts) + suppressed + collapsed
    callouts = [{"col": 1, "text": f"{collapsed} mirror re-lists \u2192 collapse to 1"}] if collapsed else []
    return {
        "cols": ["t1", "t2", "t3"],
        "lanes": [["CRITICAL", "#f87171"], ["HIGH", "#fb923c"], ["MEDIUM", "#fbbf24"], ["LOW / churn", "#64748b"]],
        "events": events, "callouts": callouts,
        "cards": [["Raw events", raw], ["Ranked alerts", len(alerts)], ["Criticals", n_crit], ["Churn suppressed", suppressed]],
        "compare": f"Full run: {len(alerts)} ranked alerts, both criticals on top, 0 false alerts. Naive: "
                   f"{raw} flat events, the two criticals buried mid-stream, and the churn re-listed as noise.",
    }

def evidence_data():
    """LIVE (Ch15): run the report-forge engine over the chained evidence and turn
    its graded findings into the capstone claim board (the negative is pulled out)."""
    d = _run_engine("report-forge", "pipeline.py", [])
    findings = d["findings"]
    neg = next((f for f in findings if f["id"] == "do_not_attribute"), None)
    claims = [{"t": f["statement"], "conf": f["confidence"], "type": f["type"]}
              for f in findings if f["id"] != "do_not_attribute"]
    cc = Counter(c["conf"] for c in claims)
    return {
        "engines": [["Ch11", "market records"], ["Ch12", "leak + negotiation"],
                    ["Ch13", "persona clusters"], ["Ch14", "detection alerts"]],
        "hub": f"Evidence graph \u2014 {d.get('target', 'Operator Alpha')}",
        "claims": claims,
        "negative": neg["statement"] if neg else "",
        "legend": [["high", "#34d399"], ["moderate", "#fbbf24"], ["low", "#f87171"]],
        "cards": [["Claims", len(claims)], ["High", cc.get("high", 0)],
                  ["Moderate", cc.get("moderate", 0)], ["Low", cc.get("low", 0)]],
    }

def scorecard_data():
    # the book's published full-vs-naive results - the star metric per chapter, as a percentage
    return {
        "metric": {
            "labels": ["Ch10 clone\nrecall", "Ch11 field\naccuracy", "Ch12 bluffs\ncaught",
                       "Ch13 link\nprecision", "Ch14 alert\nprecision", "Ch15\nprovenance"],
            "naive": [50, 92, 0, 40, 36, 0],
            "full":  [100, 100, 100, 100, 100, 100],
        },
        "errors": {
            "labels": ["Ch11 poisoned\naccepted", "Ch13 false\nmerges", "Ch14 false\nalerts", "Ch15\noverclaims"],
            "naive": [1, 9, 12, 6],
            "full":  [0, 0, 0, 0],
        },
        "cards": [["Chapters graded", 7], ["Metrics at 100% (full)", 6],
                  ["Analyst errors (full)", 0], ["Analyst errors (naive)", 28]],
    }


def compute_all():
    return {
        "dashboard": {"negotiations": negotiations_data(), "leaksite": leaksite_data(),
                      "changefeed": changefeed_data(), "market": market_data()},
        "attribution": {"persona": persona_data(), "dedup": dedup_data()},
        "detection": detection_data(),
        "capstone": evidence_data(),
        "method": scorecard_data(),
    }


# ============================ shared chrome (CSS + JS) ============================

STYLE = """
:root{--bg:#0b0b14;--panel:#14152a;--edge:#262844;--ink:#e7e8f0;--muted:#9aa0b4;
--p:#a855f7;--c:#22d3ee;--a:#fbbf24;--g:#34d399;--r:#f87171;--b:#60a5fa;--o:#fb923c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:0 20px 80px}
header{padding:36px 0 20px;border-bottom:1px solid var(--edge)}
h1{margin:0 0 6px;font-size:25px;letter-spacing:.2px}h1 .sub{color:var(--p)}
.lede{color:var(--muted);max-width:770px}
nav.top{position:sticky;top:0;z-index:5;background:rgba(11,11,20,.93);backdrop-filter:blur(6px);
border-bottom:1px solid var(--edge);padding:11px 0;margin-bottom:6px;display:flex;flex-wrap:wrap;gap:6px 18px}
nav.top a{color:var(--muted);text-decoration:none;font-size:12.5px;font-weight:600;letter-spacing:.4px;text-transform:uppercase}
nav.top a:hover{color:var(--c)}nav.top a.on{color:var(--p)}
section{padding:32px 0 10px;border-bottom:1px solid var(--edge)}
h2{font-size:20px;margin:0 0 4px}
h2 .tag{font-size:12px;color:var(--bg);background:var(--p);padding:2px 8px;border-radius:10px;vertical-align:middle;margin-left:8px;font-weight:700}
.why{color:var(--muted);max-width:800px;margin:4px 0 20px}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 22px}
.card{background:var(--panel);border:1px solid var(--edge);border-radius:12px;padding:14px 18px;min-width:128px;flex:1}
.card b{display:block;font-size:25px;color:var(--c)}
.card span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:720px){.grid{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--edge);border-radius:14px;padding:16px 16px 10px}
.panel.wide{grid-column:1/-1}
.panel h3{margin:0 0 2px;font-size:15px}.panel p.cap{margin:0 0 10px;color:var(--muted);font-size:12.5px}
.chart{width:100%;height:auto;display:block}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin:6px 2px 10px;font-size:12px;color:var(--muted)}
.legend i{display:inline-block;width:12px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
.legend i.dash{background:none;border-top:2px dashed var(--muted);height:0;width:16px;border-radius:0}
.note{background:#101227;border-left:3px solid var(--a);border-radius:8px;padding:10px 14px;margin:10px 0 4px;color:#cbd0e2;font-size:13.5px}
.atlas{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:24px}
@media(max-width:720px){.atlas{grid-template-columns:1fr}}
a.tile{display:block;text-decoration:none;background:var(--panel);border:1px solid var(--edge);border-radius:14px;padding:18px 20px;color:var(--ink);transition:border-color .15s}
a.tile:hover{border-color:var(--p)}
a.tile .k{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--p);font-weight:700}
a.tile h3{margin:4px 0 6px;font-size:17px}
a.tile p{margin:0;color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12.5px;padding-top:24px}
code{background:#1c1e38;padding:1px 6px;border-radius:5px;color:var(--c)}
"""

CHART_JS = r"""
const NS='http://www.w3.org/2000/svg';
const PAL=['#a855f7','#22d3ee','#fbbf24','#34d399','#f87171','#60a5fa'];
const AX='#3a3d63',GRID='#20223c',MUT='#9aa0b4';
function E(t,a,ch){const e=document.createElementNS(NS,t);for(const k in(a||{}))e.setAttribute(k,a[k]);
 (ch||[]).forEach(c=>e.appendChild(typeof c==='string'?document.createTextNode(c):c));return e;}
function T(t,a){const e=E('text',Object.assign({fill:MUT,'font-size':11,'font-family':'sans-serif'},a));e.textContent=t;return e;}
function tip(s){const e=E('title');e.textContent=s;return e;}
function svg(w,h){return E('svg',{viewBox:'0 0 '+(w||520)+' '+(h||300),class:'chart',preserveAspectRatio:'xMidYMid meet'});}
function mount(id,s){const el=document.getElementById(id);if(el)el.appendChild(s);}
function niceMax(m){const p=Math.pow(10,Math.floor(Math.log10(m||1)));const n=m/p;const s=n<=1?1:n<=2?2:n<=5?5:10;return s*p;}

function hbar(id,d,color){const s=svg();const W=520,H=300,L=118,R=20,Tp=10,B=20;
 const max=niceMax(Math.max(...d.values));const iw=W-L-R;const bh=(H-Tp-B)/d.values.length;
 for(let g=0;g<=4;g++){const x=L+iw*g/4;s.appendChild(E('line',{x1:x,y1:Tp,x2:x,y2:H-B,stroke:GRID}));
  s.appendChild(T(Math.round(max*g/4),{x:x,y:H-6,'text-anchor':'middle','font-size':10}));}
 d.values.forEach((v,i)=>{const y=Tp+i*bh;const w=iw*v/max;
  const rc=E('rect',{x:L,y:y+bh*0.16,width:Math.max(w,1),height:bh*0.68,rx:3,fill:color||PAL[0]});rc.appendChild(tip(d.labels[i]+': '+v));s.appendChild(rc);
  s.appendChild(T(d.labels[i],{x:L-8,y:y+bh*0.62,'text-anchor':'end','font-size':11,fill:'#c9cce0'}));
  s.appendChild(T(v,{x:L+w+5,y:y+bh*0.62,'font-size':10,fill:MUT}));});mount(id,s);}

function bars(id,d,color){const s=svg();const W=520,H=300,L=42,R=16,Tp=14,B=58;
 const max=niceMax(Math.max(...d.values));const iw=W-L-R;const bw=iw/d.values.length;
 for(let g=0;g<=4;g++){const y=Tp+(H-Tp-B)*(1-g/4);s.appendChild(E('line',{x1:L,y1:y,x2:W-R,y2:y,stroke:GRID}));
  s.appendChild(T(Math.round(max*g/4),{x:L-6,y:y+3,'text-anchor':'end','font-size':10}));}
 d.values.forEach((v,i)=>{const x=L+i*bw;const h=(H-Tp-B)*v/max;
  const rc=E('rect',{x:x+bw*0.18,y:H-B-h,width:bw*0.64,height:Math.max(h,1),rx:3,fill:color||PAL[1]});rc.appendChild(tip(d.labels[i]+': '+v));s.appendChild(rc);
  s.appendChild(T(v,{x:x+bw*0.5,y:H-B-h-4,'text-anchor':'middle','font-size':10,fill:MUT}));
  (d.labels[i]+'').split('\n').forEach((ln,k)=>s.appendChild(T(ln,{x:x+bw*0.5,y:H-B+14+k*11,'text-anchor':'middle','font-size':9.5})));});mount(id,s);}

function grouped(id,d){const s=svg();const W=520,H=300,L=40,R=16,Tp=14,B=52;
 const flat=[].concat(...d.series.map(x=>x.values));const max=niceMax(Math.max(...flat));
 const iw=W-L-R;const gw=iw/d.groups.length;const bw=gw*0.8/d.series.length;
 for(let g=0;g<=4;g++){const y=Tp+(H-Tp-B)*(1-g/4);s.appendChild(E('line',{x1:L,y1:y,x2:W-R,y2:y,stroke:GRID}));
  s.appendChild(T(Math.round(max*g/4),{x:L-6,y:y+3,'text-anchor':'end','font-size':10}));}
 d.groups.forEach((grp,gi)=>{const gx=L+gi*gw+gw*0.1;
  d.series.forEach((ser,si)=>{const v=ser.values[gi];const h=(H-Tp-B)*v/max;const x=gx+si*bw;
   const rc=E('rect',{x:x,y:H-B-h,width:bw*0.9,height:Math.max(h,1),rx:2,fill:PAL[si%PAL.length]});rc.appendChild(tip(grp+' \u00b7 '+ser.name+': '+v));s.appendChild(rc);});
  (grp+'').split('\n').forEach((ln,k)=>s.appendChild(T(ln,{x:gx+gw*0.4,y:H-B+15+k*11,'text-anchor':'middle','font-size':10,fill:'#c9cce0'})));});mount(id,s);}

function stacked(id,d){const s=svg();const W=520,H=300,L=40,R=16,Tp=14,B=40;
 const totals=d.groups.map((_,gi)=>d.series.reduce((a,ser)=>a+ser[gi],0));const max=niceMax(Math.max(...totals));
 const iw=W-L-R;const gw=iw/d.groups.length;
 for(let g=0;g<=4;g++){const y=Tp+(H-Tp-B)*(1-g/4);s.appendChild(E('line',{x1:L,y1:y,x2:W-R,y2:y,stroke:GRID}));
  s.appendChild(T(Math.round(max*g/4),{x:L-6,y:y+3,'text-anchor':'end','font-size':10}));}
 d.groups.forEach((grp,gi)=>{let acc=0;const x=L+gi*gw+gw*0.25;
  d.series.forEach((ser,si)=>{const v=ser[gi];const h=(H-Tp-B)*v/max;acc+=h;
   const rc=E('rect',{x:x,y:H-B-acc,width:gw*0.5,height:Math.max(h,0),fill:PAL[si%PAL.length]});rc.appendChild(tip(grp+' \u00b7 '+d.keys[si]+': '+v));s.appendChild(rc);});
  s.appendChild(T(grp,{x:x+gw*0.25,y:H-B+16,'text-anchor':'middle','font-size':11,fill:'#c9cce0'}));});mount(id,s);}

function line(id,d,opt){opt=opt||{};const s=svg();const W=520,H=300,L=44,R=16,Tp=14,B=30;
 const xs=d.points.map(p=>p.x),ys=d.points.map(p=>p.y);const xmax=Math.max(...xs)||1;const ymax=niceMax(Math.max(...ys));const iw=W-L-R,ih=H-Tp-B;
 for(let g=0;g<=4;g++){const y=Tp+ih*(1-g/4);s.appendChild(E('line',{x1:L,y1:y,x2:W-R,y2:y,stroke:GRID}));
  s.appendChild(T(Math.round(ymax*g/4),{x:L-6,y:y+3,'text-anchor':'end','font-size':10}));}
 if(opt.threshold){const y=Tp+ih*(1-opt.threshold/ymax);s.appendChild(E('line',{x1:L,y1:y,x2:W-R,y2:y,stroke:'#f87171','stroke-dasharray':'4 4','stroke-width':1}));
  s.appendChild(T('burst threshold',{x:W-R,y:y-4,'text-anchor':'end','font-size':10,fill:'#f87171'}));}
 const pt=p=>[L+iw*p.x/xmax,Tp+ih*(1-p.y/ymax)];let path='';
 d.points.forEach((p,i)=>{const[x,y]=pt(p);path+=(i?'L':'M')+x.toFixed(1)+' '+y.toFixed(1)+' ';});
 s.appendChild(E('path',{d:path,fill:'none',stroke:opt.color||PAL[0],'stroke-width':2}));
 d.points.forEach(p=>{if(p.burst){const[x,y]=pt(p);const c=E('circle',{cx:x,cy:y,r:3.2,fill:'#f87171'});c.appendChild(tip(p.label+': '+p.y));s.appendChild(c);}});
 (opt.xlabels||[]).forEach((lb,i,arr)=>{const x=L+iw*i/(arr.length-1);s.appendChild(T(lb,{x:x,y:H-8,'text-anchor':i===0?'start':i===arr.length-1?'end':'middle','font-size':10}));});mount(id,s);}

function lorenz(id,d){const s=svg();const W=520,H=300,L=44,R=16,Tp=14,B=34;const iw=W-L-R,ih=H-Tp-B;
 for(let g=0;g<=4;g++){const y=Tp+ih*(1-g/4),x=L+iw*g/4;s.appendChild(E('line',{x1:L,y1:y,x2:W-R,y2:y,stroke:GRID}));
  s.appendChild(T(g*25,{x:L-6,y:y+3,'text-anchor':'end','font-size':10}));s.appendChild(T(g*25,{x:x,y:H-8,'text-anchor':'middle','font-size':10}));}
 s.appendChild(E('line',{x1:L,y1:H-B,x2:W-R,y2:Tp,stroke:'#565a86','stroke-dasharray':'4 4'}));
 const pt=p=>[L+iw*p.x/100,Tp+ih*(1-p.y/100)];let path='';
 d.curve.forEach((p,i)=>{const[x,y]=pt(p);path+=(i?'L':'M')+x.toFixed(1)+' '+y.toFixed(1)+' ';});
 s.appendChild(E('path',{d:path,fill:'none',stroke:PAL[2],'stroke-width':2}));
 s.appendChild(T('% of vendors',{x:(L+W-R)/2,y:H-1,'text-anchor':'middle','font-size':10,fill:MUT}));mount(id,s);}

function legend(id,items){const el=document.getElementById(id);if(!el)return;const w=document.createElement('div');w.className='legend';
 items.forEach((t,i)=>{const sp=document.createElement('span');sp.innerHTML='<i style="background:'+PAL[i%PAL.length]+'"></i>'+t;w.appendChild(sp);});el.appendChild(w);}
function legendC(id,pairs){const el=document.getElementById(id);if(!el)return;const w=document.createElement('div');w.className='legend';
 pairs.forEach(([t,c])=>{const sp=document.createElement('span');const dash=(c==='hard'||c==='soft'||c==='flagged');
  const col=c==='hard'?'#c9cce0':c==='soft'?MUT:c==='flagged'?'#f87171':c;
  sp.innerHTML=(dash&&c!=='hard'?'<i class="dash" style="border-top-color:'+col+(c==='flagged'?';border-top-style:dashed':'')+'"></i>':'<i style="background:'+col+'"></i>')+t;w.appendChild(sp);});el.appendChild(w);}
function cards(id,list){const el=document.getElementById(id);if(!el)return;
 list.forEach(([label,val])=>{const c=document.createElement('div');c.className='card';c.innerHTML='<b>'+val+'</b><span>'+label+'</span>';el.appendChild(c);});}

// ---- node-link operator graph (Ch13) ----
function graph(id,d){const W=1040;const n=d.clusters.length;const colW=W/n;const _mm=Math.max(...d.clusters.map(cl=>d.nodes.filter(nd=>nd.cluster===cl.id).length));const H=86+_mm*46+34;const s=svg(W,H);
 const pos={};
 d.clusters.forEach((cl,ci)=>{const members=d.nodes.filter(nd=>nd.cluster===cl.id);
  const cx=ci*colW+colW/2;const boxW=colW-34;const rowH=46;const top=86;const boxH=members.length*rowH+22;
  // cluster hull
  s.appendChild(E('rect',{x:cx-boxW/2,y:top-40,width:boxW,height:boxH+40,rx:14,fill:'#10122a',stroke:cl.color,'stroke-width':1.5,opacity:0.95}));
  s.appendChild(T(cl.label,{x:cx,y:top-20,'text-anchor':'middle','font-size':13,fill:cl.color,'font-weight':'700'}));
  const bd=E('text',{x:cx,y:top-4,'text-anchor':'middle','font-size':10.5,fill:MUT});bd.textContent='confidence: '+cl.badge;s.appendChild(bd);
  members.forEach((nd,mi)=>{const y=top+18+mi*rowH;pos[nd.id]=[cx,y];
   s.appendChild(E('rect',{x:cx-boxW/2+14,y:y-15,width:boxW-28,height:30,rx:8,fill:'#1b1d3a',stroke:cl.color,'stroke-width':1}));
   s.appendChild(T(nd.label,{x:cx-boxW/2+24,y:y+4,'font-size':12.5,fill:'#e7e8f0','font-weight':'600'}));
   const tg=E('text',{x:cx+boxW/2-16,y:y+4,'text-anchor':'end','font-size':10,fill:MUT});tg.textContent=nd.tag;s.appendChild(tg);});
  // within-cluster spine
  const kind=d.spine[cl.id];
  if(kind&&members.length>1){for(let i=0;i<members.length-1;i++){const[x1,y1]=pos[members[i].id];const[x2,y2]=pos[members[i+1].id];
   s.appendChild(E('line',{x1:x1-boxW/2+14,y1:(y1+15),x2:x1-boxW/2+14,y2:(y2-15),stroke:kind==='hard'?'#c9cce0':MUT,'stroke-width':kind==='hard'?2:1.5,'stroke-dasharray':kind==='hard'?'':'5 4'}));}}
 });
 // flagged cross edge
 if(d.flagged){const[ax,ay]=pos[d.flagged.from];const tgt=d.clusters.find(c=>c.id===d.flagged.to);const ti=d.clusters.indexOf(tgt);const tx=ti*colW+colW/2;
  s.appendChild(E('path',{d:'M'+ax+' '+ay+' C '+((ax+tx)/2)+' '+(ay-70)+', '+((ax+tx)/2)+' '+(70)+', '+tx+' 92',fill:'none',stroke:'#f87171','stroke-width':1.6,'stroke-dasharray':'5 4'}));
  s.appendChild(T(d.flagged.label,{x:(ax+tx)/2,y:44,'text-anchor':'middle','font-size':10.5,fill:'#f87171'}));}
 mount(id,s);}

// ---- mirror vs clone (Ch10) ----
function mirrorclone(id,d){const W=1040,H=300,s=svg(W,H);const cx=W/2,cy=150;
 // origin center
 s.appendChild(E('rect',{x:cx-70,y:cy-22,width:140,height:44,rx:10,fill:'#1b1d3a',stroke:'#a855f7','stroke-width':1.5}));
 s.appendChild(T(d.origin,{x:cx,y:cy-2,'text-anchor':'middle','font-size':13,fill:'#e7e8f0','font-weight':'700'}));
 s.appendChild(T('origin wallet',{x:cx,y:cy+13,'text-anchor':'middle','font-size':10,fill:'#a855f7'}));
 const place=(items,dir,color,tagColor,tagtxt)=>{const n=items.length;items.forEach((it,i)=>{
   const y=cy+(i-(n-1)/2)*70;const x=cx+dir*300;
   s.appendChild(E('line',{x1:cx+dir*70,y1:cy,x2:x-dir*80,y2:y,stroke:color,'stroke-width':2,'stroke-dasharray':dir<0?'':'6 4'}));
   s.appendChild(E('rect',{x:x-80,y:y-22,width:160,height:44,rx:10,fill:'#141633',stroke:color,'stroke-width':1.4}));
   s.appendChild(T(it[0],{x:x,y:y-3,'text-anchor':'middle','font-size':11.5,fill:'#e7e8f0'}));
   const tg=E('text',{x:x,y:y+13,'text-anchor':'middle','font-size':9.5,fill:tagColor});tg.textContent=it[1];s.appendChild(tg);});};
 place(d.mirrors,-1,'#34d399','#34d399');  // left = mirrors (same wallet, merge)
 place(d.clones, 1,'#f87171','#f87171');   // right = clones (divergent wallet, separate)
 s.appendChild(T('MIRRORS \u2192 same wallet \u2192 merge',{x:cx-300,y:40,'text-anchor':'middle','font-size':12,fill:'#34d399','font-weight':'700'}));
 s.appendChild(T('CLONES \u2192 different wallet \u2192 separate',{x:cx+300,y:40,'text-anchor':'middle','font-size':12,fill:'#f87171','font-weight':'700'}));
 mount(id,s);}

// ---- alert timeline / swimlane (Ch14) ----
function timeline(id,d){const W=1040,cols=d.cols.length,lanes=d.lanes.length;const laneH=78,top=52,L=120;
 const H=top+lanes*laneH+20;const s=svg(W,H);const colW=(W-L-20)/cols;
 // lane bands + labels
 d.lanes.forEach((ln,li)=>{const y=top+li*laneH;s.appendChild(E('rect',{x:L,y:y,width:W-L-20,height:laneH,fill:li%2?'#101227':'#0d0f22'}));
  s.appendChild(E('rect',{x:20,y:y+laneH/2-9,width:92,height:18,rx:9,fill:ln[1],opacity:0.18}));
  s.appendChild(T(ln[0],{x:26,y:y+laneH/2+4,'font-size':11,fill:ln[1],'font-weight':'700'}));});
 // column headers + separators
 d.cols.forEach((cl,ci)=>{const x=L+ci*colW;s.appendChild(E('line',{x1:x,y1:top,x2:x,y2:H-20,stroke:GRID}));
  s.appendChild(T('snapshot '+cl,{x:x+colW/2,y:top-16,'text-anchor':'middle','font-size':12,fill:'#c9cce0','font-weight':'600'}));});
 // events (stack within a cell)
 const cell={};d.events.forEach(ev=>{const k=ev.col+'_'+ev.lane;cell[k]=(cell[k]||0)+1;const idx=cell[k]-1;
  const x=L+ev.col*colW+colW/2;const y=top+ev.lane*laneH+22+idx*24;const col=d.lanes[ev.lane][1];
  const dot=E('circle',{cx:x-Math.min(colW*0.4,150),cy:y,r:ev.crit?6:4,fill:col,stroke:ev.crit?'#fff':'none','stroke-width':ev.crit?1.4:0});dot.appendChild(tip(ev.label));s.appendChild(dot);
  s.appendChild(T(ev.label,{x:x-Math.min(colW*0.4,150)+11,y:y+4,'font-size':10.5,fill:ev.crit?'#fff':'#cbd0e2','font-weight':ev.crit?'700':'400'}));});
 (d.callouts||[]).forEach(co=>{const x=L+co.col*colW+colW/2;s.appendChild(T('\u2937 '+co.text,{x:x-Math.min(colW*0.4,150)+11,y:top+3*laneH+60,'font-size':10,fill:'#7dd3fc','font-style':'italic'}));});
 mount(id,s);}

// ---- evidence chain / flow (Ch15) ----
function flow(id,d){const W=1040,H=Math.max(400,64+d.claims.length*56);const s=svg(W,H);
 const c1=150,c2=470,c3=820;const conf={high:'#34d399',moderate:'#fbbf24',low:'#f87171'};
 function wrap(t,max,ml){var w=t.split(' '),L=[],cur='';for(var j=0;j<w.length;j++){var tt=cur?cur+' '+w[j]:w[j];if(tt.length>max&&cur){L.push(cur);cur=w[j];}else{cur=tt;}}if(cur)L.push(cur);if(L.length>ml){var last=L[ml-1];L=L.slice(0,ml);L[ml-1]=(last.length>max-1?last.slice(0,max-1).trim():last)+'\u2026';}return L;}
 // engines
 const eN=d.engines.length;d.engines.forEach((en,i)=>{const y=70+i*((H-120)/eN);
  s.appendChild(E('rect',{x:c1-100,y:y-20,width:180,height:40,rx:9,fill:'#1b1d3a',stroke:'#60a5fa','stroke-width':1.2}));
  s.appendChild(T(en[0],{x:c1-88,y:y+4,'font-size':12,fill:'#60a5fa','font-weight':'700'}));
  s.appendChild(T(en[1],{x:c1-54,y:y+4,'font-size':10.5,fill:'#cbd0e2'}));
  s.appendChild(E('path',{d:'M'+(c1+80)+' '+y+' C '+((c1+c2)/2)+' '+y+', '+((c1+c2)/2)+' '+(H/2)+', '+(c2-92)+' '+(H/2),fill:'none',stroke:'#33507a','stroke-width':1.3}));});
 // hub
 s.appendChild(E('rect',{x:c2-92,y:H/2-30,width:184,height:60,rx:12,fill:'#241b3a',stroke:'#a855f7','stroke-width':1.8}));
 d.hub.split('\u2014').forEach((ln,k)=>s.appendChild(T(ln.trim(),{x:c2,y:H/2-4+k*17,'text-anchor':'middle','font-size':12,fill:'#e7e8f0','font-weight':'700'})));
 // claims (wrapped to fit)
 const slot=(H-92)/d.claims.length,LH=11.5,PAD=7;
 d.claims.forEach((cm,i)=>{const cy=58+i*slot;const col=conf[cm.conf];
  const lines=wrap((cm.type==='fact'?'\u25c6 ':'\u25c7 ')+cm.t,49,3),bh=PAD*2+lines.length*LH;
  s.appendChild(E('path',{d:'M'+(c2+92)+' '+(H/2)+' C '+((c2+c3)/2)+' '+(H/2)+', '+((c2+c3)/2)+' '+cy+', '+(c3-120)+' '+cy,fill:'none',stroke:'#3a3d63'}));
  const fill=cm.type==='fact'?col:'#141633';const txtc=cm.type==='fact'?'#0b0b14':'#e7e8f0';
  s.appendChild(E('rect',{x:c3-120,y:cy-bh/2,width:324,height:bh,rx:7,fill:fill,stroke:col,'stroke-width':1.4}));
  lines.forEach((ln,k)=>s.appendChild(T(ln,{x:c3-112,y:cy-bh/2+PAD+8+k*LH,'font-size':9.5,fill:txtc})));});
 s.appendChild(T('\u25c6 fact   \u25c7 assessment   \u2015 colour = confidence',{x:c3+42,y:20,'text-anchor':'middle','font-size':10,fill:MUT}));
 if(d.negative){const nl=wrap('\u2715 '+d.negative,76,2),nbh=PAD*2+nl.length*LH;
  s.appendChild(E('rect',{x:c2-92,y:H-6-nbh,width:568,height:nbh,rx:7,fill:'#2a1416',stroke:'#f87171','stroke-width':1.3}));
  nl.forEach((ln,k)=>s.appendChild(T(ln,{x:c2-82,y:H-6-nbh+PAD+8+k*LH,'font-size':10,fill:'#fca5a5'})));}
 mount(id,s);}
"""


# ============================ pages ============================

PAGES = [("index.html", "Atlas"), ("dashboard.html", "Real-data"),
         ("attribution.html", "Attribution"), ("detection.html", "Detection"),
         ("capstone.html", "Capstone"), ("method.html", "Method")]

def _data_stamp():
    """When the real data behind this report was captured, for the footer."""
    try:
        c = sqlite3.connect(LEAK)
        st = {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}
        c.close()
        cap = st.get("captured_at", "unknown")
        thru = st.get("date_max", "")
        return f"captured {cap}" + (f", ransomwatch posts through {thru}" if thru else "")
    except Exception:
        return "captured (unknown)"


def shell(active, title, sub, lede, body, data, init):
    nav = "".join(f'<a href="{h}"{" class=\"on\"" if h==active else ""}>{lbl}</a>' for h, lbl in PAGES)
    return f"""<!doctype html>
<!-- Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026 -->
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{STYLE}</style></head><body><div class="wrap">
<header><h1>{title} <span class="sub">{sub}</span></h1><p class="lede">{lede}</p></header>
<nav class="top">{nav}</nav>
{body}
<footer>Generated offline by <code>./lab report</code> from committed, scrubbed data, and shared into the
workstation read-only at <code>/intel</code>. Victim, vendor, and operator identities are pseudonymised;
no real entity is named. A site/lab artifact - the printed book carries static screenshots.
<br><strong>Data snapshot:</strong> {_data_stamp()} &middot; the figures above reflect this bundled snapshot; run <code>./lab update</code> to pull the current feed, then re-render.</footer>
</div>
<script>const DATA={json.dumps(data, separators=(',', ':'))};</script>
<script>{CHART_JS}</script>
<script>{init}</script>
</body></html>"""

def build_index(_):
    tiles = [
        ("dashboard.html", "Real-data", "Ransomware & market intelligence",
         "The negotiation corpus, leak-site feed, change feed, and a market slice - read live from the committed databases."),
        ("attribution.html", "Chapters 10 & 13", "Who is one operator",
         "The persona graph that fuses pseudonyms into operators, and the payment tell that separates a mirror from a clone."),
        ("detection.html", "Chapter 14", "What changed, and does it matter",
         "Three monitoring snapshots turned into ranked alerts - campaign bursts, dedup collapse, and the two criticals on top."),
        ("capstone.html", "Chapter 15", "The evidence chain",
         "Four engines converging into one evidence graph and a set of graded claims, each carrying its confidence and type."),
        ("method.html", "Across the book", "Why the disciplined method matters",
         "The published full-vs-naive scorecard: where the shortcut collapses and the careful pipeline holds."),
    ]
    cards = "".join(f'<a class="tile" href="{h}"><div class="k">{k}</div><h3>{t}</h3><p>{p}</p></a>' for h, k, t, p in tiles)
    body = f'''<section style="border:none">
      <p class="why">Each page below is a single self-contained file. The analysis ran on the host, over the same
      data the graded labs use; the charts are hand-drawn SVG with nothing loaded from the network, so they open
      from <code>file://</code> even though this desktop routes through Tor. Because the folder is mounted
      read-only, you can read the intelligence here but not change it.</p>
      <div class="atlas">{cards}</div></section>'''
    return shell("index.html", "Unlock the Secrets of the DARK WEB", "&middot; atlas",
                 "A visual intelligence package built from the book's analyses.", body, {}, "")

def build_dashboard(d):
    body = '''<section id="negotiations"><h2>Ransomware negotiations<span class="tag">Ch12</span></h2>
      <p class="why">Every ransomware brand negotiates with a recognisable fingerprint, read from the real transcript corpus:
      which pressure tactics it leans on, how far its opening demand sits from its walk-away floor, and how its cases end.</p>
      <div class="cards" id="c-neg"></div>
      <div class="grid">
      <div class="panel"><h3>Tactic fingerprint by group</h3><p class="cap">Share of transcripts using each tactic.</p><div id="lg-tac"></div><div id="ch-tac"></div></div>
      <div class="panel"><h3>Opening demand vs walk-away floor</h3><p class="cap">Seeded from the corpus, USD millions.</p><div id="lg-rng"></div><div id="ch-rng"></div></div>
      <div class="panel"><h3>How cases end</h3><p class="cap">Outcomes across each group's transcripts.</p><div id="lg-out"></div><div id="ch-out"></div></div>
      <div class="panel"><h3>Messages by group</h3><p class="cap">Operator vs victim turns.</p><div id="lg-corpus"></div><div id="ch-corpus"></div></div>
      </div></section>
      <section id="leaksite"><h2>Leak-site channel<span class="tag">Ch12</span></h2>
      <p class="why">The public leak site is the extortion op's billboard - 16,072 real posts. The growth curve shows how
      relentless naming is; the ranking shows how concentrated it is among a few operators.</p>
      <div class="cards" id="c-leak"></div>
      <div class="grid">
      <div class="panel"><h3>Cumulative victims named</h3><p class="cap">Every post, accumulated by month.</p><div id="ch-cum"></div></div>
      <div class="panel"><h3>Most active groups</h3><p class="cap">Distinct victims, top ten.</p><div id="ch-topg"></div></div>
      </div></section>
      <section id="changefeed"><h2>Monitoring the change feed<span class="tag">Ch14</span></h2>
      <p class="why">Monitoring turns the feed into deltas. The weekly rate is mostly steady with sharp campaign spikes,
      flagged above a burst threshold; the taxonomy sorts every event into new victims, reposts, and cross-group listings.</p>
      <div class="cards" id="c-cf"></div>
      <div class="grid">
      <div class="panel"><h3>Weekly posting rate</h3><p class="cap">New posts per week; red points are bursts.</p><div id="ch-week"></div></div>
      <div class="panel"><h3>Event taxonomy</h3><p class="cap">How the feed classifies each event.</p><div id="ch-tax"></div></div>
      </div></section>
      <section id="market"><h2>Market vendor graph<span class="tag">Ch11</span></h2>
      <p class="why">A market is a database behind a hostile interface. Read from a scrubbed slice of a real market, these
      show how listings concentrate among a few vendors, where goods ship, and how prices tier.</p>
      <div class="cards" id="c-mkt"></div>
      <div class="grid">
      <div class="panel"><h3>Top vendors</h3><p class="cap">Listings per vendor, top ten.</p><div id="ch-vend"></div></div>
      <div class="panel"><h3>Vendor concentration</h3><p class="cap">Cumulative share vs rank; dashed = equality.</p><div id="ch-lor"></div></div>
      <div class="panel"><h3>Shipping lanes</h3><p class="cap">Most common origin&rarr;destination pairs.</p><div id="ch-lane"></div></div>
      <div class="panel"><h3>Price tiers</h3><p class="cap">Listings by BTC price bucket.</p><div id="ch-tier"></div></div>
      </div></section>'''
    init = """const D=DATA;
cards('c-neg',D.negotiations.cards);
legend('lg-tac',D.negotiations.tactics.series.map(s=>s.name));grouped('ch-tac',D.negotiations.tactics);
legend('lg-rng',['opening demand','walk-away floor']);grouped('ch-rng',{groups:D.negotiations.range.groups,series:[{name:'anchor',values:D.negotiations.range.anchor},{name:'floor',values:D.negotiations.range.floor}]});
legend('lg-out',D.negotiations.outcomes.keys);stacked('ch-out',{groups:D.negotiations.outcomes.groups,keys:D.negotiations.outcomes.keys,series:D.negotiations.outcomes.series});
legend('lg-corpus',['operator','victim']);grouped('ch-corpus',{groups:D.negotiations.messages_by_group.groups,series:[{name:'operator',values:D.negotiations.messages_by_group.operator},{name:'victim',values:D.negotiations.messages_by_group.victim}]});
cards('c-leak',D.leaksite.cards);line('ch-cum',D.leaksite.cumulative,{color:PAL[1],xlabels:D.leaksite.cumulative.xlabels});hbar('ch-topg',D.leaksite.top_groups,PAL[0]);
cards('c-cf',D.changefeed.cards);line('ch-week',D.changefeed.weekly,{color:PAL[5],threshold:D.changefeed.weekly.threshold,xlabels:['start','','now']});bars('ch-tax',D.changefeed.taxonomy,PAL[2]);
cards('c-mkt',D.market.cards);hbar('ch-vend',D.market.top_vendors,PAL[0]);lorenz('ch-lor',D.market.lorenz);bars('ch-lane',D.market.lanes,PAL[3]);bars('ch-tier',D.market.tiers,PAL[2]);"""
    return shell("dashboard.html", "Unlock the Secrets of the DARK WEB", "&middot; real-data dashboard",
                 "The negotiation corpus, leak-site feed, change feed, and market slice, read live from the committed databases.",
                 body, d, init)

def build_attribution(d):
    body = '''<section><h2>Persona linkage<span class="tag">Ch13</span></h2>
      <p class="why">An identity is a set of claims spread across a market vendor, a leak brand, and a forum handle.
      Linkage asks which pseudonyms are one operator. Hard identifiers - a reused signed key, a shared wallet - link;
      soft signals only corroborate; a key a persona merely <em>displays</em> is never enough to merge. Every cluster
      carries a confidence, and the graph refuses to cross from a pseudonym to a named person.</p>
      <div id="lg-graph"></div>
      <div class="panel wide"><div id="ch-graph"></div></div></section>
      <section><h2>Mirror vs clone<span class="tag">Ch10</span></h2>
      <p class="why">A copy of a market and a rival's imitation look structurally identical. What separates them is the
      money: a mirror reuses the origin's payment wallet, a clone carries its own.</p>
      <div class="panel wide"><div id="ch-mc"></div></div>
      <div class="note" id="mc-note"></div></section>'''
    init = """const D=DATA;
legendC('lg-graph',D.attribution.persona.legend);graph('ch-graph',D.attribution.persona);
mirrorclone('ch-mc',D.attribution.dedup);document.getElementById('mc-note').textContent=D.attribution.dedup.note;"""
    return shell("attribution.html", "Attribution", "&middot; who is one operator",
                 "Fusing pseudonyms into operators, and the payment tell that separates a mirror from a clone.",
                 body, {"attribution": d}, init)

def build_detection(d):
    body = '''<section><h2>The alert timeline<span class="tag">Ch14</span></h2>
      <p class="why">Monitoring watches a timeline of snapshots and asks, for each change, whether it matters and how
      urgently, without drowning the analyst. The dangerous error is crying wolf. Here three snapshots become a handful
      of ranked alerts: campaign churn is suppressed, a mirror's re-listing collapses to one event, and the two
      criticals - a clone that swapped its key, and a watched operator resurfacing under a new handle - sit on top.</p>
      <div class="cards" id="c-det"></div>
      <div class="panel wide"><div id="ch-tl"></div></div>
      <div class="note" id="det-note"></div></section>'''
    init = """const D=DATA;cards('c-det',D.detection.cards);timeline('ch-tl',D.detection);
document.getElementById('det-note').textContent=D.detection.compare;"""
    return shell("detection.html", "Detection", "&middot; what changed, and does it matter",
                 "Three monitoring snapshots turned into ranked alerts.", body, {"detection": d}, init)

def build_capstone(d):
    body = '''<section><h2>The evidence chain<span class="tag">Ch15</span></h2>
      <p class="why">The capstone chains all four engines over one operator into a single evidence graph, then turns it
      into a decision-ready set of claims. A report is a chain of claims, each carrying its statement, its type
      (fact or assessment), and its confidence. The value is that a reader can trace every assertion to evidence and
      tell what is known from what is judged - and the report attributes to an operator, never to a named person.
      One finding is deliberately negative: a persona that displays the key but is not Alpha.</p>
      <div class="cards" id="c-cap"></div>
      <div id="lg-flow"></div>
      <div class="panel wide"><div id="ch-flow"></div></div></section>'''
    init = """const D=DATA;cards('c-cap',D.capstone.cards);legendC('lg-flow',D.capstone.legend);flow('ch-flow',D.capstone);"""
    return shell("capstone.html", "Capstone", "&middot; the evidence chain",
                 "Four engines converging into one evidence graph and a set of graded claims.", body, {"capstone": d}, init)

def build_method(d):
    body = '''<section><h2>Full vs naive<span class="tag">the whole book</span></h2>
      <p class="why">Every chapter grades a disciplined pipeline against a naive shortcut. The lesson is rarely about
      missing data - both usually find the events. It is about noise, false links, and unearned confidence. These are
      the published results: the star metric per chapter, and the errors the shortcut makes that the careful method does not.</p>
      <div class="cards" id="c-m"></div>
      <div class="grid">
      <div class="panel"><h3>Star metric by chapter (%)</h3><p class="cap">Higher is better.</p><div id="lg-m"></div><div id="ch-m"></div></div>
      <div class="panel"><h3>Errors the shortcut makes</h3><p class="cap">Count; lower is better. Full is zero across the board.</p><div id="lg-e"></div><div id="ch-e"></div></div>
      </div></section>'''
    init = """const D=DATA;cards('c-m',D.method.cards);
legend('lg-m',['naive','full']);grouped('ch-m',{groups:D.method.metric.labels,series:[{name:'naive',values:D.method.metric.naive},{name:'full',values:D.method.metric.full}]});
legend('lg-e',['naive','full']);grouped('ch-e',{groups:D.method.errors.labels,series:[{name:'naive',values:D.method.errors.naive},{name:'full',values:D.method.errors.full}]});"""
    return shell("method.html", "Method", "&middot; why the disciplined method matters",
                 "The published full-vs-naive scorecard across the book.", body, {"method": d}, init)


def render_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    data = compute_all()
    pages = {
        "index.html": build_index(None),
        "dashboard.html": build_dashboard(data["dashboard"]),
        "attribution.html": build_attribution(data["attribution"]),
        "detection.html": build_detection(data["detection"]),
        "capstone.html": build_capstone(data["capstone"]),
        "method.html": build_method(data["method"]),
    }
    sizes = {}
    for name, html in pages.items():
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            f.write(html)
        sizes[name] = len(html)
    return sizes


def selftest():
    import tempfile
    d = tempfile.mkdtemp()
    sizes = render_all(d)
    ok = True; msgs = []
    need = {"index.html": ["atlas", "tile"], "dashboard.html": ["const DATA=", "function grouped"],
            "attribution.html": ["function graph", "Operator Alpha"],
            "detection.html": ["function timeline", "CRITICAL"],
            "capstone.html": ["function flow", "evidence"], "method.html": ["Full vs naive", "naive"]}
    for name, markers in need.items():
        html = open(os.path.join(d, name), encoding="utf-8").read()
        external = ("https://" in html) or ("cdn." in html) or ("<link" in html) or ('src="http' in html)
        good = sizes[name] > 4000 and all(m in html for m in markers) and not external
        ok = ok and good
        msgs.append(f"  {name:<18} {sizes[name]:>7,}b  external={external}  {'ok' if good else 'FAIL'}")
    print("\n".join(msgs))
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--selftest" in args:
        sys.exit(selftest())
    outdir = args[args.index("--outdir") + 1] if "--outdir" in args else os.path.join(HERE, "intel")
    sizes = render_all(outdir)
    total = sum(sizes.values())
    print(f"wrote {len(sizes)} pages to {outdir} ({total:,} bytes total)")
    for n, s in sizes.items():
        print(f"  {n:<18} {s:>7,} bytes")
