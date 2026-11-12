"""IndicIntentGuard live demo.

Browser mic -> Gnani Prisma -> guard decision -> (if needed) Gnani Timbre asks a targeted
confirmation -> caller's spoken reply -> Prisma -> mock execution.

  uvicorn app.server:app --port 8000
"""
import json
import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indicintentguard import ledger  # noqa: E402
from indicintentguard.clarify import VOICES, build_prompt, interpret_reply  # noqa: E402
from indicintentguard.config import CACHE_DIR, DATA  # noqa: E402
from indicintentguard.evidence import Observation, compute  # noqa: E402
from indicintentguard.gnani import synthesize, transcribe  # noqa: E402
from indicintentguard.numbers import spell_amount  # noqa: E402
from indicintentguard.policies import POLICIES  # noqa: E402
from indicintentguard.risk import INTENT_RISK, RiskModel  # noqa: E402
from indicintentguard.schemas import Action, Decision  # noqa: E402

STATIC = Path(__file__).parent / "static"
UPLOADS = DATA / "uploads"
MAX_REPLY_ROUNDS = 2

app = FastAPI(title="IndicIntentGuard")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

model_path = DATA / "risk_model.json"
MODEL = RiskModel.load(model_path) if model_path.exists() else RiskModel()
SESSIONS: dict[str, dict] = {}
EXECUTED: list[dict] = []
OPENING_BALANCE = 200_000  # mock passbook
BALANCE = OPENING_BALANCE


def _save_upload(f: UploadFile) -> Path:
    UPLOADS.mkdir(parents=True, exist_ok=True)
    data = f.file.read()
    if len(data) > 5_000_000:
        raise HTTPException(413, "Audio too large (max ~60 s)")
    p = UPLOADS / f"{uuid.uuid4().hex[:12]}{Path(f.filename or 'a.wav').suffix or '.wav'}"
    p.write_bytes(data)
    return p


def _audio_source(audio: UploadFile | None, sample: str | None) -> Path:
    if audio is not None:
        return _save_upload(audio)
    if sample:
        p = (DATA / "raw" / Path(sample).name)
        if p.exists():
            return p
    raise HTTPException(400, "Send an audio file or pick a sample")


def _speak(text: str, lang: str) -> str | None:
    tts_lang, voice, model = VOICES.get(lang, VOICES["en-IN"])
    try:
        r = synthesize(text, language=tts_lang, voice=voice, model=model)
    except Exception as e:  # demo still works (text prompt) if TTS fails or budget is hit
        print("Timbre error:", e)
        return None
    return "/tts/" + Path(r["path"]).name


def _execute(action: Action, via: str) -> dict:
    global BALANCE
    rec = {"time": time.strftime("%H:%M:%S"), "via": via, **action.model_dump(exclude_none=True)}
    rec["intent"] = action.intent.value
    if action.intent.value == "transfer" and action.amount:
        BALANCE -= action.amount
    rec["balance"] = BALANCE
    EXECUTED.insert(0, rec)
    return rec


def _view(action: Action | None) -> dict | None:
    if action is None:
        return None
    d = action.model_dump(exclude_none=True)
    d.pop("extra", None)
    if action.amount is not None:
        d["words"] = spell_amount(action.amount)
    return d


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/tts/{name}")
def tts_file(name: str):
    p = CACHE_DIR / "timbre" / Path(name).name
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="audio/wav")


@app.get("/sample/{name}")
def sample_file(name: str):
    p = DATA / "raw" / Path(name).name
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="audio/wav")


@app.get("/api/samples")
def samples():
    out = []
    for f in sorted(DATA.glob("labels/*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                if (DATA / "raw" / d["audio_file"]).exists():
                    out.append({"file": d["audio_file"], "text": d["reference_transcript"], "gold": d["action"],
                                "synthetic": "synthetic" in d.get("tags", [])})
    seen, uniq = set(), []
    for s in out:
        if s["file"] not in seen:
            seen.add(s["file"])
            uniq.append(s)
    return uniq


@app.get("/api/state")
def state():
    return {"executed": EXECUTED[:20], "ledger": ledger.summary(),
            "opening_balance": OPENING_BALANCE, "balance": BALANCE}


@app.post("/api/analyze")
def analyze(
    audio: UploadFile | None = File(None),
    sample: str | None = Form(None),
    language_code: str = Form("en-IN"),
    reply_lang: str = Form("en-IN"),
    max_amount: int | None = Form(200000),
    known_accounts: str = Form(""),
):
    path = _audio_source(audio, sample)
    try:
        r = transcribe(path, language_code, "transcribe")
    except ledger.BudgetExceeded as e:
        raise HTTPException(402, str(e))
    except Exception as e:
        raise HTTPException(502, f"Prisma error: {str(e)[:300]}")

    ctx = {"max_amount": max_amount} if max_amount else {}
    accts = [a.strip() for a in known_accounts.split(",") if a.strip()]
    if accts:
        ctx["known_accounts"] = accts
    obs = Observation.from_prisma(r, audio_path=str(path), ctx=ctx)
    parsed, features, _ = compute(obs)
    outs = {name: pol(obs, MODEL) for name, pol in POLICIES.items()}
    g = outs["B3_guard"]
    tier = INTENT_RISK.get(g.action.intent.value if g.action else "other", "medium")

    resp = {
        "transcript": obs.transcript, "literal": obs.literal, "latency_ms": r["latency_ms"],
        "cached": r["cached"], "audio_stats": obs.audio_stats,
        "features": {k: v for k, v in features.items() if v},
        "weights": {k: MODEL.w.get(k, 0.0) for k, v in features.items() if v},
        "probability": MODEL.prob(features),
        "threshold": MODEL.threshold(tier) if tier in MODEL.error_cost else 0.0,
        "tier": tier,
        "superseded": parsed.superseded,
        "policies": {n: {"decision": o.decision.value, "action": _view(o.action)} for n, o in outs.items()},
        "guard": {"decision": g.decision.value, "reasons": g.reasons[:-1], "fields": g.fields_to_confirm,
                  "action": _view(g.action)},
    }
    if g.decision == Decision.accept and g.action:
        resp["executed"] = _execute(g.action, "auto-accepted")
    elif g.decision == Decision.clarify:
        sid = uuid.uuid4().hex[:10]
        prompt = build_prompt(g.action, g.fields_to_confirm, reply_lang)
        SESSIONS[sid] = {"action": g.action, "fields": g.fields_to_confirm, "lang": reply_lang,
                         "prisma_lang": language_code, "rounds": 0}
        resp["clarify"] = {"session": sid, "prompt": prompt, "audio": _speak(prompt, reply_lang)}
    return resp


@app.post("/api/reply")
def reply(session: str = Form(...), audio: UploadFile | None = File(None), text: str | None = Form(None)):
    s = SESSIONS.get(session)
    if not s:
        raise HTTPException(404, "Unknown or finished session")
    heard = text or ""
    if audio is not None:
        try:
            r = transcribe(_save_upload(audio), s["prisma_lang"], "transcribe")
        except ledger.BudgetExceeded as e:
            raise HTTPException(402, str(e))
        heard = r["transcript"]
    pending: Action | None = s["action"]
    if pending is None:
        # Nothing parsed earlier: treat the reply as a fresh request for the missing value.
        from indicintentguard.extract import parse
        new = parse(heard, naive=False).action
        status, result = ("corrected", new) if new else ("unclear", None)
    else:
        status, result = interpret_reply(heard, pending)
    s["rounds"] += 1
    out = {"heard": heard, "status": status}

    if status == "confirmed":
        out["executed"] = _execute(result, "confirmed by caller")
        SESSIONS.pop(session, None)
    elif status == "rejected":
        out["message"] = "Cancelled. Nothing was executed."
        SESSIONS.pop(session, None)
    elif status == "corrected" and s["rounds"] <= MAX_REPLY_ROUNDS:
        s["action"] = result
        prompt = build_prompt(result, s["fields"] or ["amount"], s["lang"])
        out["clarify"] = {"session": session, "prompt": prompt, "audio": _speak(prompt, s["lang"])}
        out["action"] = _view(result)
    elif s["rounds"] > MAX_REPLY_ROUNDS or status == "unclear" and s["rounds"] >= MAX_REPLY_ROUNDS:
        out["status"] = "escalated"
        out["message"] = "Could not confirm after two tries. Escalated to a human agent; nothing executed."
        SESSIONS.pop(session, None)
    else:
        prompt = build_prompt(pending, s["fields"] or ["amount"], s["lang"])
        out["clarify"] = {"session": session, "prompt": prompt, "audio": _speak(prompt, s["lang"])}
    return out
