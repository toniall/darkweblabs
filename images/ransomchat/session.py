#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
RansomChat session state — the negotiation's fixed facts, and the guard that
keeps the operator inside them.

Why this module exists
----------------------
The first version of the chat let the language model own the negotiation's
facts. Every turn re-sent the persona prompt, which said "open near $X", so the
model re-executed that instruction on every reply: it greeted the victim again
mid-session, and it invented a new anchor (and sometimes a new group name) each
time. A transcript like that is not analysable — Chapter 12's offer staircase
and the bluff in the gap both assume a single stable opening demand.

The fix is structural, and it is the same discipline the chapter teaches about
extracted records: do not let a generative process own a field you need to
reason over. The group, the anchor, the floor and the deadline are drawn ONCE
when the session starts, stored server-side, and stated to the model as fixed
facts. The operator's opening turn is a template, not a generation. Anything the
model produces that contradicts the session facts is caught on the way out.

This module is deliberately free of Flask so it can be self-tested offline and
in CI, where the chat container is not running.

Usage:
  python3 session.py --selftest
"""
import json, os, re, sqlite3, sys, threading, uuid, datetime

# ── the model's standing instructions, appended to every system prompt ────────
GUARD = (
    " You must never provide real malware, ransomware, encryption or decryption code, "
    "exploits, or any operational help to attack systems. If asked for any of that, refuse "
    "briefly and return to negotiating. Keep replies to a few sentences, like a chat."
)

# Sent as an extra system turn when a reply broke the session facts and we retry.
CORRECTION = (
    "Your last reply broke the session facts. Do not introduce yourself again, do not "
    "name any group other than the one you are, and do not quote any figure above the "
    "opening demand you already made. Continue the negotiation already in progress."
)

# The operator's opening turn. Templated, never generated, so the anchor at the
# top of the staircase is exact and matches the group's public leak-site claim.
OPENING = (
    "This is {group} support. Your network is ours and we hold {data_gb} GB of your files. "
    "The price for the decryptor and for deleting our copy is ${anchor:,}. "
    "You have {days} days, {hours} hours, to answer before we publish you on our blog. "
    "Tell us what you are prepared to pay."
)

_MULT = {"k": 1_000, "m": 1_000_000, "mil": 1_000_000, "million": 1_000_000}
# Figures the operator states: "$1,100,000", "$80k", "1,100,000 USD", "3.45 million".
_MONEY = re.compile(
    r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(k|m|mil|million)?|"
    r"\b(\d[\d,]*(?:\.\d+)?)\s*(k|m|mil|million)?\s*(?:usd|dollars)\b",
    re.I,
)


def _value(num, unit):
    try:
        v = float(str(num).replace(",", ""))
    except ValueError:
        return None
    return v * _MULT.get((unit or "").lower(), 1)


# ── session facts, drawn once from the behaviour DB ───────────────────────────
def load_profile(db_path, group):
    """Return the fixed facts for one group, or None if the group is unknown.

    Everything here comes from structured columns the seeder derived from the
    Casualtek corpus. The stored free-text persona prompt is used only for the
    group's voice; the numbers come from the columns, so the chat and the
    analyser cannot disagree about them.
    """
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT name, demand_min, demand_median, deadline_days, "
        "synthetic_public_claim, chat_persona, style_lines FROM groups WHERE name=?",
        (group,),
    ).fetchone()
    if not row:
        return None
    name, dmin, dmed, dl, public, persona, style = row
    public = json.loads(public or "{}")
    persona = json.loads(persona or "{}")
    anchor = int(public.get("demand_usd") or dmed or 500_000)
    # The negotiated floor. Real settlements in the corpus land far below the
    # opening ask, so a quarter of the anchor is a fair bottom; never below the
    # group's own observed minimum, never above the anchor.
    floor = max(int(anchor * 0.25), int(dmin or 0))
    floor = min(floor, anchor)
    rivals = [r[0] for r in con.execute("SELECT name FROM groups WHERE name<>?", (name,))]
    return {
        "group": name,
        "anchor": anchor,
        "floor": floor,
        "deadline_days": int(dl or public.get("deadline_days") or 3),
        "data_gb": int(public.get("data_gb") or 400),
        "top_tactics": public.get("typical_tactics", []),
        "voice": persona.get("system_prompt", ""),
        "style": [s["line"] for s in json.loads(style or "[]")][:6],
        "rivals": rivals,
    }


def build_system_prompt(p):
    """The operator's system prompt: role, then the fixed facts, then the voice."""
    lines = [
        f"You are role-playing the negotiator ('support') for the {p['group']} ransomware group, "
        f"for a DEFENSIVE TRAINING exercise. The user is the victim's negotiator, learning to "
        f"recognise extortion tactics. Stay strictly inside the negotiation: apply pressure, "
        f"offer proof, concede slowly, in {p['group']}'s style.",
        "",
        "SESSION FACTS. These are fixed for the whole conversation and you must never contradict them:",
        f"  - You are {p['group']}. Never name, mention, or claim to represent any other group.",
        f"  - Your opening demand was ${p['anchor']:,} and you have ALREADY made it. The negotiation "
        f"is in progress, not starting.",
        f"  - Never quote a figure above ${p['anchor']:,}. You may concede downwards in steps, and "
        f"never below ${p['floor']:,}.",
        f"  - The deadline is {p['deadline_days']} days from the start of this chat. You may threaten "
        f"it, you may slide it, but it is the only deadline.",
        f"  - You hold {p['data_gb']} GB of the victim's files.",
        "  - Never greet the victim again, never re-introduce yourself, and never restate the opening "
        "demand as though it were new.",
    ]
    if p["style"]:
        lines += [
            "",
            "Examples of this group's real phrasing (imitate the tone, not the exact words):",
            *("  - " + s.replace("\n", " ").strip() for s in p["style"]),
        ]
    return "\n".join(lines) + GUARD


def opening_text(p):
    return OPENING.format(
        group=p["group"], data_gb=p["data_gb"], anchor=p["anchor"],
        days=p["deadline_days"], hours=p["deadline_days"] * 24,
    )


# ── the outbound consistency guard ───────────────────────────────────────────
def enforce(reply, p):
    """Check one operator reply against the session facts.

    Returns (corrected_reply, violations). The correction is deliberately blunt,
    a rival group name becomes this session's group and a figure above the
    anchor is pulled back to the anchor, because an internally inconsistent
    transcript is worse than a slightly clipped one: the analyser reads the
    staircase as data. The caller should retry the model once before applying it.
    """
    violations = []
    out = reply

    for rival in p.get("rivals", []):
        if re.search(rf"\b{re.escape(rival)}\b", out, re.I):
            violations.append(f"named rival group {rival}")
            out = re.sub(rf"\b{re.escape(rival)}\b", p["group"], out, flags=re.I)

    def clamp(m):
        num, unit = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        val = _value(num, unit)
        if val is not None and val > p["anchor"]:
            violations.append(f"quoted ${int(val):,} above the ${p['anchor']:,} anchor")
            return f"${p['anchor']:,}"
        return m.group(0)

    out = _MONEY.sub(clamp, out)
    return out, violations


# ── the session store ────────────────────────────────────────────────────────
class SessionStore:
    """In-memory sessions. A restart of the container drops them, and the client
    simply starts a new one, which is the right behaviour for a training chat."""

    def __init__(self):
        self._d = {}
        self._lock = threading.Lock()

    def start(self, profile, backend):
        sid = uuid.uuid4().hex[:16]
        now = datetime.datetime.now(datetime.timezone.utc)
        opening = opening_text(profile)
        with self._lock:
            self._d[sid] = {
                "id": sid,
                "profile": profile,
                "backend": backend,
                "system": build_system_prompt(profile),
                "started": now.isoformat().replace("+00:00", "Z"),
                "messages": [{"party": "operator", "content": opening,
                              "ts": now.isoformat().replace("+00:00", "Z")}],
            }
        return self._d[sid]

    def get(self, sid):
        with self._lock:
            return self._d.get(sid)

    def append(self, sid, party, content):
        s = self.get(sid)
        if not s:
            return None
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        with self._lock:
            s["messages"].append({"party": party, "content": content, "ts": ts})
        return s

    def drop(self, sid):
        with self._lock:
            self._d.pop(sid, None)


def transcript(sess):
    """The saved session in the Casualtek schema the analyser already reads."""
    group = sess["profile"]["group"]
    started = sess["started"]
    return {
        "chat_id": started[:16].replace("-", "").replace(":", "").replace("T", "-")[:13],
        "group": group,
        "backend": sess["backend"],
        "started": started,
        "anchor_usd": sess["profile"]["anchor"],
        "deadline_days": sess["profile"]["deadline_days"],
        "messages": [
            {"party": ("Victim" if m["party"] == "victim" else group),
             "content": "> " + m["content"], "timestamp": m.get("ts", "")}
            for m in sess["messages"]
        ],
    }


# ── self-test ────────────────────────────────────────────────────────────────
def _selftest():
    ok = True

    def t(name, cond):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + name)
        ok = ok and bool(cond)

    p = {"group": "Akira", "anchor": 1_100_000, "floor": 275_000, "deadline_days": 3,
         "data_gb": 400, "top_tactics": [], "voice": "", "style": ["We will publish."],
         "rivals": ["Conti", "REvil"]}

    sysmsg = build_system_prompt(p)
    t("system prompt pins the group", "You are Akira." in sysmsg)
    t("system prompt pins the anchor", "$1,100,000" in sysmsg)
    t("system prompt pins the floor", "$275,000" in sysmsg)
    t("system prompt forbids re-greeting", "never re-introduce" in sysmsg.lower())
    t("system prompt keeps the safety guard", "never provide real malware" in sysmsg)

    op = opening_text(p)
    t("templated opening carries the exact anchor", "$1,100,000" in op)
    t("templated opening carries the deadline", "3 days" in op and "72 hours" in op)

    # the exact failure this module exists to prevent
    bad = ("You have connected to our secure channel. I represent Conti ransomware group. "
           "Initial offer: 3,450,000 USD within the next 72 hours.")
    fixed, v = enforce(bad, p)
    t("guard catches the rival group name", any("Conti" in x for x in v))
    t("guard catches the figure above the anchor", any("above" in x for x in v))
    t("guard rewrites the rival name away", "Conti" not in fixed)
    t("guard pulls the figure back to the anchor", "$1,100,000" in fixed)

    good = "We can come down to $800,000 if you pay this week. That is a real discount."
    fixed2, v2 = enforce(good, p)
    t("a legitimate concession is left alone", fixed2 == good and not v2)
    at_anchor = "The price is $1,100,000 and it does not change."
    t("a quote at the anchor is left alone", enforce(at_anchor, p) == (at_anchor, []))
    t("k-suffixed figures are read", _value("80", "k") == 80_000)

    store = SessionStore()
    s = store.start(p, "ollama")
    t("a new session opens with exactly one operator turn",
      len(s["messages"]) == 1 and s["messages"][0]["party"] == "operator")
    store.append(s["id"], "victim", "I need help")
    store.append(s["id"], "operator", "Then make an offer.")
    s = store.get(s["id"])
    t("the session accumulates the turns", len(s["messages"]) == 3)
    doc = transcript(s)
    t("the transcript uses the Casualtek schema",
      doc["group"] == "Akira" and doc["messages"][0]["party"] == "Akira"
      and doc["messages"][1]["party"] == "Victim"
      and doc["messages"][0]["content"].startswith("> "))
    t("the transcript records the pinned anchor", doc["anchor_usd"] == 1_100_000)

    # against the shipped DB, if it is reachable from here
    db = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "..", "labs", "artifacts", "ransomchat", "negotiations.db")
    if os.path.exists(db):
        pr = load_profile(db, "Akira")
        t("Akira loads from the shipped DB", pr and pr["group"] == "Akira")
        t("Akira's anchor matches its public claim", pr and pr["anchor"] == 1_100_000)
        t("the floor sits under the anchor", pr and 0 < pr["floor"] < pr["anchor"])
        t("rivals are the other two groups", pr and set(pr["rivals"]) == {"Conti", "REvil"})

    print("\n  selftest " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(__doc__)
