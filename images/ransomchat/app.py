#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
RansomChat — a DEFENSIVE-TRAINING negotiation simulator for Chapter 12.

Serves a helpdesk-style chat where the reader (the victim's negotiator) talks to
an operator persona for Akira / Conti / REvil, seeded from negotiations.db, which
was built from the public Casualtek corpus. The operator can be driven by three
backends chosen in the UI: OpenAI, xAI Grok, or a local Ollama container.

The operator is constrained to negotiation role-play only and refuses to produce
malware, encryption code, or any operational attack help.

State model
-----------
The negotiation's facts (group, opening demand, floor, deadline, data volume)
live in a SERVER-SIDE session, not in the model and not in the browser. The
client holds a session id and nothing else that matters. See session.py for why:
letting the model own those fields produced transcripts that changed group and
anchor mid-conversation, which the Chapter 12 analyser cannot read.
"""
import os, json, sqlite3, urllib.request
from flask import Flask, request, jsonify, Response

from session import (SessionStore, load_profile, enforce, transcript,
                     CORRECTION)

APP = Flask(__name__)
DB = os.environ.get("CHAT_DB", "/app/negotiations.db")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "8192"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
XAI_KEY = os.environ.get("XAI_API_KEY", "")
SAVE_DIR = os.environ.get("CHAT_SAVE_DIR", "/evidence/negotiations")
TEMP = float(os.environ.get("CHAT_TEMPERATURE", "0.7"))

STORE = SessionStore()


def db():
    return sqlite3.connect(DB)


# ── backend calls ────────────────────────────────────────────────────────────
def to_openai_messages(system, history, correction=None):
    msgs = [{"role": "system", "content": system}]
    for m in history:
        msgs.append({"role": "assistant" if m["party"] == "operator" else "user",
                     "content": m["content"]})
    if correction:
        msgs.append({"role": "system", "content": correction})
    return msgs


def call_openai(url, key, model, system, history, correction=None):
    body = json.dumps({"model": model,
                       "messages": to_openai_messages(system, history, correction),
                       "max_tokens": 300, "temperature": TEMP}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"].strip()


def call_ollama(system, history, correction=None):
    # num_ctx is set explicitly: Ollama's default 2048 silently drops the oldest
    # tokens, which here means the system prompt, taking the session facts with it.
    body = json.dumps({"model": OLLAMA_MODEL,
                       "messages": to_openai_messages(system, history, correction),
                       "stream": False,
                       "options": {"temperature": TEMP, "num_ctx": OLLAMA_CTX}}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    return d["message"]["content"].strip()


def generate(backend, system, history, correction=None):
    if backend == "openai":
        if not OPENAI_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set (put it in .env before ./lab ransomchat up)")
        return call_openai("https://api.openai.com/v1/chat/completions", OPENAI_KEY,
                           os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                           system, history, correction)
    if backend == "grok":
        if not XAI_KEY:
            raise RuntimeError("XAI_API_KEY is not set (put it in .env before ./lab ransomchat up)")
        return call_openai("https://api.x.ai/v1/chat/completions", XAI_KEY,
                           os.environ.get("XAI_MODEL", "grok-2-latest"),
                           system, history, correction)
    return call_ollama(system, history, correction)


def operator_turn(sess):
    """One guarded operator reply: generate, check against the session facts,
    retry once with a correction, then rewrite whatever still disagrees."""
    prof, system, history = sess["profile"], sess["system"], sess["messages"]
    reply = generate(sess["backend"], system, history)
    reply, violations = enforce(reply, prof)
    if violations:
        try:
            retry = generate(sess["backend"], system, history, CORRECTION)
            retry, retry_violations = enforce(retry, prof)
            if not retry_violations:
                reply, violations = retry, []
            else:
                reply, violations = retry, retry_violations
        except Exception:  # noqa: BLE001 — a failed retry keeps the corrected first reply
            pass
    if violations:
        APP.logger.warning("session %s consistency guard: %s", sess["id"], "; ".join(violations))
    return reply, violations


# ── API ──────────────────────────────────────────────────────────────────────
@APP.route("/api/groups")
def groups():
    rows = db().execute("SELECT name, n_transcripts FROM groups ORDER BY n_transcripts DESC").fetchall()
    return jsonify([{"name": n, "transcripts": t} for n, t in rows])


@APP.route("/api/session", methods=["POST"])
def start_session():
    """Open a negotiation. The group, anchor, floor and deadline are drawn here,
    once, and never change for the life of the session. The operator's opening
    turn is templated from them rather than generated."""
    data = request.get_json(force=True, silent=True) or {}
    group = data.get("group", "Akira")
    backend = data.get("backend", "ollama")
    prof = load_profile(DB, group)
    if not prof:
        return jsonify({"error": f"unknown group {group}"}), 400
    sess = STORE.start(prof, backend)
    return jsonify({
        "session_id": sess["id"],
        "group": prof["group"],
        "anchor_usd": prof["anchor"],
        "deadline_days": prof["deadline_days"],
        "data_gb": prof["data_gb"],
        "opening": sess["messages"][0]["content"],
    })


@APP.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    sid = data.get("session_id")
    sess = STORE.get(sid) if sid else None
    if not sess:
        # the container restarted, or the tab is older than the session store
        return jsonify({"error": "session expired", "restart": True}), 404
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify({"error": "empty message"}), 400
    if data.get("backend"):
        sess["backend"] = data["backend"]
    STORE.append(sid, "victim", text)
    try:
        reply, violations = operator_turn(sess)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f'{sess["backend"]} backend error: {e}'}), 502
    STORE.append(sid, "operator", reply)
    return jsonify({"party": "operator", "content": reply, "guard": violations})


@APP.route("/api/save", methods=["POST"])
def save():
    data = request.get_json(force=True)
    sess = STORE.get(data.get("session_id"))
    if not sess:
        return jsonify({"error": "session expired", "restart": True}), 404
    doc = transcript(sess)
    fname = f'{doc["chat_id"]}-{doc["group"]}.json'
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(os.path.join(SAVE_DIR, fname), "w") as f:
            json.dump(doc, f, indent=2)
        saved = os.path.join(SAVE_DIR, fname)
    except Exception:  # noqa: BLE001
        saved = None
    return jsonify({"saved": saved, "filename": fname, "transcript": doc})


@APP.route("/")
def index():
    return Response(open("/app/chat.html").read(), mimetype="text/html")


@APP.route("/health")
def health():
    try:
        n = db().execute("SELECT COUNT(*) FROM groups").fetchone()[0]
        return jsonify({"ok": True, "groups": n})
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=8090, threaded=True)
