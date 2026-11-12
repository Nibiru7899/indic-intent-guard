"""Gnani Timbre TTS client (REST, returns raw audio bytes).

Docs: https://docs.gnani.ai/api/TTS/tts-inference
Spell out numbers before calling ("thirteen thousand rupees", not "13000"):
the docs warn raw digits/currency may be mispronounced.
"""
import json
import time
from pathlib import Path

import requests

from .. import cache, ledger
from ..config import get_settings


def synthesize(
    text: str,
    language: str = "en-IN",
    voice: str | None = None,
    model: str | None = None,
    sample_rate: int = 16000,
    use_cache: bool = True,
    timeout: float = 60.0,
) -> dict:
    """Return {"path", "latency_ms", "cached"}; audio is written as WAV into the cache."""
    s = get_settings()
    body = {
        "text": text,
        "model": model or s.timbre_model,
        "voice": voice or s.timbre_voice,
        "language": language,
        "audio_config": {"sample_rate": sample_rate, "num_channels": 1, "sample_width": 2,
                         "encoding": "linear_pcm", "container": "wav"},
    }
    key = cache.key_for(text.encode("utf-8"), {k: v for k, v in body.items() if k != "text"})
    out_path = cache.path_for("timbre", key, "wav")

    if use_cache and out_path.exists():
        return {"path": str(out_path), "latency_ms": None, "cached": True, "request": body}

    if not s.api_key:
        raise RuntimeError("GNANI_API_KEY is not set in .env")
    ledger.check_budget(s.max_api_calls)

    t0 = time.perf_counter()
    resp = requests.post(
        s.timbre_url,
        headers={"X-API-Key-ID": s.api_key, "Content-Type": "application/json"},
        data=json.dumps(body),
        timeout=timeout,
    )
    latency_ms = (time.perf_counter() - t0) * 1000
    is_audio = resp.ok and not resp.headers.get("Content-Type", "").startswith("application/json")

    ledger.record({
        "service": "timbre",
        "params": {k: v for k, v in body.items() if k != "text"},
        "chars": len(text),
        "status": resp.status_code,
        "ok": is_audio,
        "latency_ms": round(latency_ms, 1),
        "cache_key": key,
    })

    if not is_audio:
        raise requests.HTTPError(f"Timbre {resp.status_code}: {resp.text[:1000]}", response=resp)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(resp.content)
    return {"path": str(out_path), "latency_ms": round(latency_ms, 1), "cached": False, "request": body}
