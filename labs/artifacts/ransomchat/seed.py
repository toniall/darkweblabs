#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Build negotiations.db from the Casualtek/Ransomchats corpus (Akira, Conti, REvil).

The DB is COMMITTED to the repo pre-built, so a reader never needs to run this.
It exists for reproducibility: it fetches the public transcripts, scrubs residual
PII, tags every operator turn with Chapter 12's tactic taxonomy, and derives a
per-group behaviour profile that seeds both the chat operator and the analysis.

Usage:
  python3 seed.py [--src DIR] [--out negotiations.db] [--selftest]

With --src, reads transcripts from a local clone (DIR/<Group>/*.json).
Without it, shallow-clones Casualtek/Ransomchats into a temp dir.

Source: https://github.com/Casualtek/Ransomchats  (public, already redacts
wallets/URLs). This seeder adds a conservative second scrub pass; company/victim
names in free text are best-effort only and should be reviewed by the author.
"""
import sqlite3, json, re, sys, os, glob, subprocess, tempfile, statistics

GROUPS = ["Akira", "Conti", "REvil"]
REPO = "https://github.com/Casualtek/Ransomchats.git"
RAW = "https://raw.githubusercontent.com/Casualtek/Ransomchats/main/{g}/{f}"

# ── Chapter 12 tactic taxonomy (extends leak-extract/negotiation.py _TACTICS) ──
TACTICS = {
 "deadline_pressure": r"(deadline|\b\d+\s*(hour|day)s?\b|time is|waste (our|my) time|running out|expire|final (offer|price)|last chance|end of the (week|term))",
 "threat_leak":       r"(publish|leak|\bblog\b|release your|to the media|journalist|sell (your|it)|competitor|public domain|disclose|auction)",
 "threat_notify":     r"(notify|inform|contact|call).{0,25}(client|staff|customer|partner|patient|regulator|public)",
 "proof_offered":     r"(test (file|decrypt)|proof|\bsample\b|file[- ]?list|choose \d|select \d|decrypt.{0,8}files? (for|to)|prove)",
 "deletion_promise":  r"(delet(e|ion)|destroy|remove your|non-recoverable|wiped?|erase)",
 "discount_offer":    r"(discount|reduce|lower the|special price|meet you|good will|-?\d+\s*%|concession)",
 "payment_split":     r"(split|installment|two payment|in parts|deposit|pay.{0,10}(now|later|rest))",
 "reassurance":       r"(reputation|we always|guarantee|our word|you can trust|honest|business|not interested in your data)",
 "authority_defer":   r"(my boss|management|the boss|talked to|our team decided|superior|our conditions do not change)",
}
TACTIC_DESC = {
 "deadline_pressure":"A time threat to force a fast, uncounselled decision.",
 "threat_leak":"Threat to publish, sell, or auction the stolen data.",
 "threat_notify":"Threat to tell the victim's clients, staff, or regulators.",
 "proof_offered":"Offer of a test decryption or a file list as proof of life.",
 "deletion_promise":"Promise to delete the stolen data after payment.",
 "discount_offer":"A price reduction offered as a concession.",
 "payment_split":"Offer to split the ransom into a deposit and instalments.",
 "reassurance":"An appeal to reputation or 'we always deliver'.",
 "authority_defer":"Deferring to a boss or team to shift or harden a price.",
}

def scrub(text):
    """Conservative PII pass on top of Casualtek's existing redaction."""
    text = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', '[email]', text)
    text = re.sub(r'https?://\S+', '[url]', text)
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[ip]', text)
    text = re.sub(r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,60}\b', '[wallet]', text)
    text = re.sub(r'\b0x[a-fA-F0-9]{40}\b', '[wallet]', text)
    # long bare digit runs (case/account/phone) but leave money figures alone
    text = re.sub(r'(?<![\$\d,.])\b\d{7,}\b(?!\s*(?:usd|btc|gb|k|mil))', '[num]', text, flags=re.I)
    return text.strip()

_MULT = {"k":1_000, "mil":1_000_000, "million":1_000_000, "m":1_000_000}
def amounts_usd(text):
    """Extract dollar-ish figures from a turn, normalized to USD integers."""
    out = []
    for m in re.finditer(r'\$?\s?([\d][\d,\.]{2,})\s*(usd|k|mil|million|m|btc)?', text.lower()):
        raw = m.group(1).replace(",", "")
        unit = (m.group(2) or "").strip()
        if unit == "btc":
            continue  # BTC handled separately; USD is the negotiable figure
        try:
            val = float(raw)
        except ValueError:
            continue
        val *= _MULT.get(unit, 1)
        if 1000 <= val <= 100_000_000:          # plausible ransom range
            out.append(int(val))
    return out

def tag(text):
    t = text.lower()
    return sorted(k for k, p in TACTICS.items() if re.search(p, t))

def deadline_days(text):
    m = re.search(r'\b(\d{1,2})\s*days?\b', text.lower())
    return int(m.group(1)) if m else None

def norm_party(party, group):
    p = party.strip().lower()
    return "victim" if p == "victim" else "operator"

def load_transcripts(src):
    """Yield (group, chat_id, filename, messages[]) for the 3 groups."""
    for g in GROUPS:
        for path in sorted(glob.glob(os.path.join(src, g, "*.json"))):
            try:
                doc = json.load(open(path, encoding="utf-8"))
            except Exception:
                continue
            msgs = doc.get("messages") or []
            if not msgs:
                continue
            yield g, os.path.basename(path)[:-5], os.path.basename(path), msgs

def build(src, out):
    if os.path.exists(out):
        os.remove(out)
    db = sqlite3.connect(out)
    c = db.cursor()
    c.executescript("""
      CREATE TABLE groups(
        name TEXT PRIMARY KEY, n_transcripts INT, tactic_freq TEXT,
        opening_examples TEXT, demand_min INT, demand_median INT, demand_max INT,
        deadline_days INT, outcomes TEXT, synthetic_public_claim TEXT,
        chat_persona TEXT, style_lines TEXT, notes TEXT);
      CREATE TABLE transcripts(
        chat_id TEXT, group_name TEXT, n_messages INT, n_operator INT,
        opening TEXT, first_demand INT, last_demand INT, outcome TEXT,
        source_url TEXT, PRIMARY KEY(chat_id, group_name));
      CREATE TABLE messages(
        group_name TEXT, chat_id TEXT, seq INT, party TEXT,
        content TEXT, tactics TEXT, amounts TEXT);
      CREATE TABLE tactics_ref(tactic TEXT PRIMARY KEY, pattern TEXT, description TEXT);
    """)
    for t, p in TACTICS.items():
        c.execute("INSERT INTO tactics_ref VALUES(?,?,?)", (t, p, TACTIC_DESC[t]))

    per_group = {g: {"tx": 0, "tactic_tx": {}, "openings": [], "demands": [],
                     "deadlines": [], "outcomes": {}, "style": []} for g in GROUPS}

    for g, cid, fname, msgs in load_transcripts(src):
        gp = per_group[g]
        gp["tx"] += 1
        n_op = 0
        opening = None
        demands_here = []
        seen_tactics = set()
        outcome = "ongoing"
        for seq, m in enumerate(msgs):
            party = norm_party(m.get("party", ""), g)
            content = scrub(re.sub(r'^\s*>\s?', '', m.get("content", "")))
            if not content:
                continue
            tags = tag(content) if party == "operator" else []
            amts = amounts_usd(content) if party == "operator" else []
            c.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?)",
                      (g, cid, seq, party, content, json.dumps(tags), json.dumps(amts)))
            if party == "operator":
                n_op += 1
                if opening is None:
                    opening = content[:400]
                for tg in tags:
                    seen_tactics.add(tg)
                demands_here += amts
                dd = deadline_days(content)
                if dd:
                    gp["deadlines"].append(dd)
                # collect representative style lines (short, tactic-bearing)
                if tags and 20 <= len(content) <= 240 and len(gp["style"]) < 60:
                    gp["style"].append({"line": content, "tactics": tags})
            low = content.lower()
            if re.search(r'\b(settl|paid|deal|we agree|payment received|deposit received)\b', low):
                outcome = "settled"
            elif re.search(r'\b(publish|leaked|posted on our|released)\b', low) and outcome != "settled":
                outcome = "published"
        first_demand = max(demands_here[:3]) if demands_here else None
        last_demand = min(demands_here) if demands_here else None  # concession = lowest reached
        src_url = f"https://github.com/Casualtek/Ransomchats/blob/main/{g}/{fname}"
        c.execute("INSERT INTO transcripts VALUES(?,?,?,?,?,?,?,?,?)",
                  (cid, g, len(msgs), n_op, opening, first_demand, last_demand, outcome, src_url))
        for tg in seen_tactics:
            gp["tactic_tx"][tg] = gp["tactic_tx"].get(tg, 0) + 1
        if opening:
            gp["openings"].append(opening)
        if first_demand:
            gp["demands"].append(first_demand)
        gp["outcomes"][outcome] = gp["outcomes"].get(outcome, 0) + 1

    # ── derive per-group profiles ────────────────────────────────────────────
    for g, gp in per_group.items():
        n = max(gp["tx"], 1)
        freq = {t: round(gp["tactic_tx"].get(t, 0) / n, 2) for t in TACTICS}
        dem = sorted(gp["demands"])
        dmin = dem[0] if dem else None
        dmed = int(statistics.median(dem)) if dem else None
        dmax = dem[-1] if dem else None
        dl = int(statistics.median(gp["deadlines"])) if gp["deadlines"] else 7
        openings = gp["openings"][:5]
        # synthetic public leak-site claim, derived from the group's real behaviour
        top_tactics = sorted(freq, key=freq.get, reverse=True)[:3]
        public_claim = {
            "headline": f"{g} has added a new victim to its leak site",
            "data_gb": 400 if g == "Akira" else (300 if g == "Conti" else 1000),
            "demand_usd": dmed or dmin or 500000,
            "deadline_days": dl,
            "threat": "publish and sell the stolen data unless paid",
            "typical_tactics": top_tactics,
        }
        # LLM persona (the chat operator's system prompt seed)
        anchor = dmed or dmin or 500000
        floor = min(max(int(anchor * 0.25), dmin or 0), anchor)
        persona = {
            "group": g,
            "opening_style": openings[0] if openings else "",
            "demand_band_usd": [dmin, dmed, dmax],
            "anchor_usd": anchor,
            "floor_usd": floor,
            "deadline_days": dl,
            "top_tactics": top_tactics,
            # The prompt states the negotiation's facts as ALREADY SETTLED. An
            # earlier version instructed the model to "open near $X", which it
            # re-executed on every turn: it greeted the victim again mid-session
            # and re-anchored at a new figure, which destroys the offer staircase
            # the Chapter 12 analyser reads. The chat container composes the
            # runtime prompt from the structured columns (see
            # images/ransomchat/session.py); this string carries the voice.
            "system_prompt": (
                f"You are role-playing the negotiator ('support') for the {g} ransomware group, "
                f"for a DEFENSIVE TRAINING exercise. The user is the victim's negotiator learning to "
                f"recognise extortion tactics. Stay strictly in the negotiation: apply pressure, offer "
                f"proof and discounts in {g}'s style. Your opening demand of ${anchor:,} has ALREADY "
                f"been made and the negotiation is in progress: never greet the victim again, never "
                f"re-introduce yourself, and never quote a figure above ${anchor:,}. Concede slowly and "
                f"never below ${floor:,}. The deadline is {dl} days and it is the only deadline. Never "
                f"name any group other than {g}. NEVER provide real malware, encryption code, exploits, "
                f"or any operational attack help; if asked, refuse and steer back to the negotiation. "
                f"This is a simulation over a synthetic scenario."
            ),
        }
        c.execute("""UPDATE groups SET n_transcripts=?, tactic_freq=?, opening_examples=?,
                     demand_min=?, demand_median=?, demand_max=?, deadline_days=?, outcomes=?,
                     synthetic_public_claim=?, chat_persona=?, style_lines=?, notes=?
                     WHERE name=?""",
                  (gp["tx"], json.dumps(freq), json.dumps(openings), dmin, dmed, dmax, dl,
                   json.dumps(gp["outcomes"]), json.dumps(public_claim), json.dumps(persona),
                   json.dumps(gp["style"][:40]),
                   "Derived from the Casualtek/Ransomchats corpus; PII-scrubbed; training use.",
                   g)) if c.execute("SELECT 1 FROM groups WHERE name=?", (g,)).fetchone() else \
        c.execute("""INSERT INTO groups(name,n_transcripts,tactic_freq,opening_examples,demand_min,
                     demand_median,demand_max,deadline_days,outcomes,synthetic_public_claim,
                     chat_persona,style_lines,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (g, gp["tx"], json.dumps(freq), json.dumps(openings), dmin, dmed, dmax, dl,
                   json.dumps(gp["outcomes"]), json.dumps(public_claim), json.dumps(persona),
                   json.dumps(gp["style"][:40]),
                   "Derived from the Casualtek/Ransomchats corpus; PII-scrubbed; training use."))
    c.execute("CREATE TABLE IF NOT EXISTS stats(key TEXT PRIMARY KEY, value TEXT)")
    import datetime as _dt   # provenance + freshness stamp (historical corpus)
    c.execute("INSERT OR REPLACE INTO stats VALUES(?,?)", ("captured_at", json.dumps(_dt.date.today().isoformat())))
    c.execute("INSERT OR REPLACE INTO stats VALUES(?,?)", ("source", json.dumps(REPO)))
    db.commit()
    return db

def clone_to_temp():
    d = tempfile.mkdtemp(prefix="ransomchats-")
    subprocess.run(["git", "clone", "--depth", "1", "--quiet", REPO, d], check=True)
    return d

def selftest(out):
    db = sqlite3.connect(out)
    c = db.cursor()
    ng = c.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    nt = c.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0]
    nm = c.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    ok = ng == 3 and nt >= 90 and nm >= 1000
    for g in GROUPS:
        row = c.execute("SELECT synthetic_public_claim, chat_persona FROM groups WHERE name=?", (g,)).fetchone()
        ok = ok and row and json.loads(row[0]).get("demand_usd") and json.loads(row[1]).get("system_prompt")
    # no raw emails/urls/ips leaked into messages
    leak = c.execute("SELECT COUNT(*) FROM messages WHERE content LIKE '%http://%' OR content LIKE '%https://%' OR content GLOB '*[a-z]@[a-z]*.[a-z]*'").fetchone()[0]
    ok = ok and leak == 0
    print(f"groups={ng} transcripts={nt} messages={nm} url/email leaks={leak}")
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    args = sys.argv[1:]
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "negotiations.db")
    if "--out" in args:
        out = args[args.index("--out") + 1]
    if "--selftest" in args and "--src" not in args and "--build" not in args:
        sys.exit(selftest(out))
    src = args[args.index("--src") + 1] if "--src" in args else None
    cleanup = False
    if not src:
        print("cloning Casualtek/Ransomchats ...")
        src = clone_to_temp(); cleanup = True
    print(f"building {out} from {src} ...")
    build(src, out)
    if cleanup:
        subprocess.run(["rm", "-rf", src])
    sys.exit(selftest(out))
