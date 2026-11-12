"""Black-box evidence for "is this extracted action wrong?".

Prisma exposes no confidence, word timings or n-best (checked against REST and WebSocket
docs, 2026-10-27). So every signal here comes from what a hosted ASR *does* return:
  - text evidence      : correction/negation structure, ambiguity, truncation
  - self-consistency   : `transcript` (ITN) vs `output.literal` from the SAME call
  - acoustic evidence  : bandwidth and SNR estimated from the audio we sent
  - context evidence   : application constraints (limits, known accounts)
"""
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .extract import Parse, parse
from .numbers import confusable_alternative

FEATURES = (
    "correction_resolved", "multiple_unresolved", "negated_only", "itn_literal_mismatch",
    "confusable_amount", "confusable_x_degraded", "truncated", "low_word_rate",
    "narrowband", "low_snr", "missing_field", "context_violation",
)


@dataclass
class Observation:
    transcript: str                       # Prisma `transcript` (ITN when format=transcribe)
    literal: str | None = None            # Prisma `output.literal` (verbatim), if present
    audio_path: str | None = None
    audio_stats: dict | None = None
    ctx: dict = field(default_factory=dict)   # {"max_amount": int, "known_accounts": [...], "risk": {...}}

    @classmethod
    def from_prisma(cls, result: dict, audio_path: str | None = None, ctx: dict | None = None) -> "Observation":
        raw = result.get("raw", result)
        literal = (raw.get("output") or {}).get("literal")
        return cls(transcript=result.get("transcript") or raw.get("transcript", ""), literal=literal,
                   audio_path=audio_path, ctx=ctx or {})


def audio_stats(path: str | Path) -> dict:
    """Effective bandwidth (99% energy roll-off) and a frame-energy SNR estimate."""
    import soundfile as sf
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    duration = len(x) / sr
    n = 512
    frames = x[: len(x) // n * n].reshape(-1, n) if len(x) >= n else x[None, :]
    spec = np.abs(np.fft.rfft(frames * np.hanning(frames.shape[1]), axis=1)) ** 2
    psd = spec.sum(axis=0)
    freqs = np.fft.rfftfreq(frames.shape[1], 1 / sr)
    # Phone audio has (almost) nothing above ~3.4-4 kHz, even if later upsampled to 16 kHz.
    hi = psd[freqs >= 4200].sum()
    hf_db = float(10 * np.log10(hi / (psd.sum() or 1) + 1e-12)) if sr > 8400 else -120.0
    e = 10 * np.log10(np.mean(frames ** 2, axis=1) + 1e-12)
    snr_db = float(np.percentile(e, 95) - np.percentile(e, 10))
    return {"sr": sr, "duration": round(duration, 2), "hf_energy_db": round(hf_db, 1), "snr_db": round(snr_db, 1)}


REQUIRED = {"transfer": ("amount",), "create_request": ("amount",)}
_TAIL_OK = {"ok", "ji", "na", "hai", "ha", "to", "do", "me", "ka", "ki", "ko", "se", "is", "it", "go", "no"}


def compute(obs: Observation) -> tuple[Parse, dict[str, float], list[str]]:
    """Return (correction-aware parse, feature vector, human-readable reasons)."""
    p = parse(obs.transcript, naive=False)
    f = dict.fromkeys(FEATURES, 0.0)
    why: list[str] = []
    a = p.action

    if any(fl.endswith("correction_resolved") for fl in p.flags):
        f["correction_resolved"] = 1
        why.append(f"self-correction detected; superseded {p.superseded}")
    if any(fl.endswith("multiple_unresolved") for fl in p.flags):
        f["multiple_unresolved"] = 1
        why.append("several values mentioned with no clear correction")
    if any(fl.endswith("negated_only") for fl in p.flags):
        f["negated_only"] = 1
        why.append("the only value mentioned is negated")

    lp = parse(obs.literal, naive=False) if obs.literal else None
    if lp and a and lp.action and (a.amount != lp.action.amount or a.account_id != lp.action.account_id):
        f["itn_literal_mismatch"] = 1
        why.append(f"Prisma's ITN and literal outputs disagree "
                   f"(amount {a.amount} vs {lp.action.amount}, account {a.account_id} vs {lp.action.account_id})")

    # ITN digits hide the spoken words, so check confusability on the literal when we have it.
    span = p.amount_span
    if lp and lp.amount_span is not None and span is not None and lp.amount_span.value == span.value:
        span = lp.amount_span
    if span is not None and span.confusable:
        f["confusable_amount"] = 1
        why.append(f"amount contains a teen/ty word; easily misheard as {confusable_alternative(span)}")

    toks = p.tokens
    if toks and len(toks[-1]) <= 2 and toks[-1].isascii() and toks[-1].isalpha() and toks[-1] not in _TAIL_OK:
        f["truncated"] = 1
        why.append(f"utterance looks cut off (ends with '{toks[-1]}')")

    st = obs.audio_stats or (audio_stats(obs.audio_path) if obs.audio_path else None)
    if st:
        obs.audio_stats = st
        if st["hf_energy_db"] < -45:
            f["narrowband"] = 1
            why.append(f"telephone-band audio ({st['sr']} Hz, {st['hf_energy_db']} dB above 4.2 kHz)")
        if st["snr_db"] < 20:
            f["low_snr"] = 1
            why.append(f"noisy audio (SNR ~{st['snr_db']} dB)")
        if st["duration"] > 1.5 and len(toks) / st["duration"] < 0.8:
            f["low_word_rate"] = 1
            why.append("few words for the audio length (possible dropped words)")
    f["confusable_x_degraded"] = f["confusable_amount"] * max(f["narrowband"], f["low_snr"])

    if a is None:
        f["missing_field"] = 1
        why.append("no actionable request recognised")
    else:
        missing = [k for k in REQUIRED.get(a.intent.value, ()) if getattr(a, k) is None]
        if missing:
            f["missing_field"] = 1
            why.append(f"missing {', '.join(missing)}")
        mx = obs.ctx.get("max_amount")
        known = obs.ctx.get("known_accounts")
        if mx is not None and a.amount is not None and a.amount > mx:
            f["context_violation"] = 1
            why.append(f"amount {a.amount} exceeds the account limit {mx}")
        if known and a.account_id and not any(k.endswith(a.account_id) for k in known):
            f["context_violation"] = 1
            why.append(f"account ...{a.account_id} is not one of the caller's accounts")
    return p, f, why
