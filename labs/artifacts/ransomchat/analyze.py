#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Analyze a saved negotiation transcript (Casualtek schema) the same way Chapter 12
reads the real corpus: extract the offer staircase, tag the operator's tactics,
and find the bluffs — both WITHIN the transcript and against the group's public
leak-site posture (the "bluff in the gap"). Closes the loop for a reader's own
RansomChat session.

Usage:
  python3 analyze.py <transcript.json> [--db negotiations.db] [--json]
  python3 analyze.py --selftest
"""
import json, re, sys, os, sqlite3
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "negotiations.db")

# Reuse the seeder's taxonomy so tags match the corpus exactly.
sys.path.insert(0, HERE)
from seed import TACTICS, amounts_usd, tag, scrub, deadline_days  # noqa: E402

FINAL = re.compile(r"\b(final (offer|price)|non[- ]?negotiable|last (offer|price|chance)|our conditions do not change|this is the best|will not (go|reduce) (lower|further))\b", re.I)
DEADLINE_CLAIM = re.compile(r"\b(publish|leak|release|start (to )?upload|post).{0,40}\b(\d+)\s*(hour|day)s?\b|\b(\d+)\s*(hour|day)s?\b.{0,30}\b(publish|leak|deadline|to negotiate)\b", re.I)
SELL = re.compile(r"\b(sell|auction|competitor|buyer|public domain|media|publish)\b", re.I)
DELETE = re.compile(r"\b(delet(e|ion)|destroy|non-recoverable|wiped?|erase)\b", re.I)
GB = re.compile(r"\b(\d{2,4})\s*gb\b", re.I)


def load(path):
    doc = json.load(open(path, encoding="utf-8"))
    group = doc.get("group") or doc.get("ransom_group") or "unknown"
    turns = []
    for seq, m in enumerate(doc.get("messages", [])):
        party = "victim" if (m.get("party", "").strip().lower() == "victim") else "operator"
        content = scrub(re.sub(r"^\s*>\s?", "", m.get("content", "")))
        if content:
            turns.append({"seq": seq, "party": party, "content": content})
    return doc, group, turns


def profile(group):
    if not os.path.exists(DB):
        return None
    row = sqlite3.connect(DB).execute(
        "SELECT tactic_freq, synthetic_public_claim FROM groups WHERE name=?", (group,)).fetchone()
    if not row:
        return None
    return {"tactic_freq": json.loads(row[0]), "public": json.loads(row[1])}


def staircase(op_turns):
    seq = []
    for t in op_turns:
        a = amounts_usd(t["content"])
        if a:
            seq.append(max(a))                       # the headline figure that turn
    # keep monotone-ish demand path: first appearance + each new lower low
    path, low = [], None
    for v in seq:
        if not path:
            path.append(v); low = v
        elif v < low:
            path.append(v); low = v
    return path, seq


def analyze(path):
    doc, group, turns = load(path)
    ops = [t for t in turns if t["party"] == "operator"]
    vics = [t for t in turns if t["party"] == "victim"]
    prof = profile(group)

    tac = Counter()
    for t in ops:
        for tg in tag(t["content"]):
            tac[tg] += 1

    path_demands, all_demands = staircase(ops)
    opening = path_demands[0] if path_demands else (max(all_demands) if all_demands else None)
    floor = min(all_demands) if all_demands else None

    # ── intra-transcript bluffs ─────────────────────────────────────────────
    bluffs = []
    final_at = next((t for t in ops if FINAL.search(t["content"]) and amounts_usd(t["content"])), None)
    if final_at:
        fval = max(amounts_usd(final_at["content"]))
        lower = [t for t in ops if t["seq"] > final_at["seq"] and amounts_usd(t["content"]) and max(amounts_usd(t["content"])) < fval]
        if lower:
            bluffs.append(("price", f'called ${fval:,} "final" (turn {final_at["seq"]}) then dropped to ${max(amounts_usd(lower[0]["content"])):,} (turn {lower[0]["seq"]})'))
    dl_at = next((t for t in ops if DEADLINE_CLAIM.search(t["content"])), None)
    if dl_at:
        after = [t for t in turns if t["seq"] > dl_at["seq"]]
        if len(after) >= 3:
            bluffs.append(("deadline", f'threatened a hard deadline (turn {dl_at["seq"]}) but the chat continued for {len(after)} more turns'))
    sells = any(SELL.search(t["content"]) for t in ops)
    dels = any(DELETE.search(t["content"]) for t in ops)
    if sells and dels:
        bluffs.append(("deletion", 'promises to DELETE the data yet also threatens to SELL/publish it — both cannot be true'))
    gbs = [int(m) for t in ops for m in GB.findall(t["content"])]
    if len(set(gbs)) > 1:
        bluffs.append(("volume", f'the stolen-data volume claim changes across the chat: {sorted(set(gbs))} GB'))

    # ── the bluff in the gap: session (private) vs public leak-site posture ──
    gap = []
    if prof:
        pub = prof["public"]
        if opening and pub.get("demand_usd") and abs(opening - pub["demand_usd"]) > 0.15 * pub["demand_usd"]:
            softer = "softer" if opening < pub["demand_usd"] else "harder"
            gap.append(f'public demand ${pub["demand_usd"]:,}  vs  private opening ${opening:,}  [{softer} in private]')
        if final_at and floor and pub.get("demand_usd") and floor < pub["demand_usd"]:
            gap.append(f'public price presented as firm  vs  private floor ${floor:,}  [the firmness was negotiable]')
        if dl_at and len([t for t in turns if t["seq"] > dl_at["seq"]]) >= 3:
            gap.append(f'public {pub.get("deadline_days","?")}-day deadline threat  vs  private willingness to keep talking past it  [deadline theatre]')
        if sells and dels:
            gap.append('public threat to sell/leak  vs  private promise to delete  [the deletion promise is hollow]')

    # ── authenticity vs the real group ──────────────────────────────────────
    auth = None
    if prof:
        freq = prof["tactic_freq"]
        used = [t for t in tac if freq.get(t, 0) >= 0.4]
        auth = {"used": used, "freq": {t: freq.get(t, 0) for t in used}}

    report = {
        "group": group, "backend": doc.get("backend"),
        "turns": {"operator": len(ops), "victim": len(vics)},
        "staircase": path_demands, "opening": opening, "floor": floor,
        "tactics": dict(tac.most_common()),
        "bluffs": bluffs, "gap": gap, "authenticity": auth,
        "thin": len(ops) < 4,
    }
    return report


def render(r):
    L = []
    L.append(f'Negotiation analysis  (group: {r["group"]}' + (f', backend: {r["backend"]}' if r["backend"] else '') + ')')
    L.append("")
    if r["thin"]:
        L.append("  too few operator turns to profile — negotiate a few more rounds, then re-run.")
        return "\n".join(L)
    L.append(f'  turns             {r["turns"]["operator"]} operator, {r["turns"]["victim"]} victim')
    if r["staircase"]:
        s = " -> ".join(f'${v:,}' for v in r["staircase"])
        conc = ""
        if len(r["staircase"]) > 1 and r["staircase"][0]:
            conc = f'  (conceded {100 - round(100*r["staircase"][-1]/r["staircase"][0])}%)'
        L.append(f'  offer staircase   {s}{conc}')
    L.append("")
    L.append("  tactics used (operator):")
    for t, n in r["tactics"].items():
        L.append(f'    {t:20} x{n}')
    L.append("")
    L.append(f'  bluffs found (within the transcript): {len(r["bluffs"])}')
    for kind, msg in r["bluffs"]:
        L.append(f'    [{kind}] {msg}')
    if r["gap"]:
        L.append("")
        L.append("  the bluff in the gap  (private session vs the group's public leak-site posture):")
        for g in r["gap"]:
            L.append(f'    {g}')
    if r["authenticity"] and r["authenticity"]["used"]:
        L.append("")
        L.append("  authenticity vs the real corpus:")
        used = ", ".join(r["authenticity"]["used"])
        L.append(f'    your operator leaned on: {used}')
        fr = ", ".join(f'{t} {int(100*v)}%' for t, v in r["authenticity"]["freq"].items())
        L.append(f'    the real {r["group"]} corpus uses those in: {fr}  -> behaved authentically')
    return "\n".join(L)


def selftest():
    sample = os.path.join(HERE, "sample-session.json")
    r = analyze(sample)
    kinds = {k for k, _ in r["bluffs"]}
    ok = (r["group"] == "Akira"
          and not r["thin"]
          and len(r["staircase"]) >= 2
          and {"price", "deadline", "deletion"} <= kinds
          and len(r["gap"]) >= 2
          and "proof_offered" in r["tactics"])
    print(render(r))
    print()
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if len(sys.argv) < 2:
        print("usage: analyze.py <transcript.json> [--json]"); sys.exit(2)
    r = analyze(sys.argv[1])
    print(json.dumps(r, indent=2) if "--json" in sys.argv else render(r))
