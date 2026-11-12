"""Gnani Prisma v2.5 STT client (REST, synchronous, clips <= 30-60 s).

Docs: https://docs.gnani.ai/api/STT/speech-to-text
Every response is cached on disk with request metadata; cached hits cost nothing.
"""
import json
import time
from pathlib import Path

import requests
import soundfile as sf

from .. import cache, ledger
from ..config import get_settings


def transcribe(
    audio_path: str | Path,
    language_code: str,
    fmt: str = "verbatim",
    extra: dict | None = None,
    use_cache: bool = True,
    timeout: float = 60.0,
) -> dict:
    """Return {"transcript", "raw", "latency_ms", "cached", ...}. Raises on HTTP error."""
    s = get_settings()
    audio_path = Path(audio_path)
    audio = audio_path.read_bytes()
    params = {"language_code": language_code, "format": fmt, **(extra or {})}
    key = cache.key_for(audio, params)
    out_path = cache.path_for("prisma", key, "json")

    if use_cache and out_path.exists():
        result = json.loads(out_path.read_text(encoding="utf-8"))
        result["cached"] = True
        return result

    if not s.api_key:
        raise RuntimeError("GNANI_API_KEY is not set in .env")
    ledger.check_budget(s.max_api_calls)

    try:
        duration = sf.info(str(audio_path)).duration
    except Exception:
        duration = None

    t0 = time.perf_counter()
    resp = requests.post(
        s.prisma_url,
        headers={"X-API-Key-ID": s.api_key},
        files={"audio_file": (audio_path.name, audio)},
        data={k: (json.dumps(v) if isinstance(v, (list, dict)) else str(v)) for k, v in params.items()},
        timeout=timeout,
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    try:
        body = resp.json()
    except ValueError:
        body = {"non_json_body": resp.text[:2000]}

    ledger.record({
        "service": "prisma",
        "file": audio_path.name,
        "params": params,
        "status": resp.status_code,
        "ok": resp.ok,
        "audio_seconds": duration,
        "latency_ms": round(latency_ms, 1),
        "cache_key": key,
    })

    if not resp.ok:
        raise requests.HTTPError(f"Prisma {resp.status_code}: {body}", response=resp)

    result = {
        "transcript": body.get("transcript", ""),
        "raw": body,  # keep everything: we need to know which fields exist
        "params": params,
        "file": audio_path.name,
        "audio_seconds": duration,
        "latency_ms": round(latency_ms, 1),
        "cache_key": key,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["cached"] = False
    return result
