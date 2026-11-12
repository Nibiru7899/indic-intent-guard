"""Append-only log of every real (uncached) Gnani API call, plus a hard budget guard.

Credits per call are not published, so the ledger records call counts and audio
seconds; compare against the dashboard balance to derive the real cost.
"""
import json
import time
from pathlib import Path

from .config import LEDGER_PATH


class BudgetExceeded(RuntimeError):
    pass


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def call_count(path: Path = LEDGER_PATH) -> int:
    return len(_read(path))


def check_budget(max_calls: int, path: Path = LEDGER_PATH) -> None:
    used = call_count(path)
    if used >= max_calls:
        raise BudgetExceeded(
            f"{used} API calls already logged (MAX_API_CALLS={max_calls}). "
            "Raise MAX_API_CALLS in .env only if you mean to spend more credits."
        )


def record(entry: dict, path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **entry}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def summary(path: Path = LEDGER_PATH) -> dict:
    rows = _read(path)
    out: dict = {"calls": len(rows), "by_service": {}}
    for r in rows:
        s = out["by_service"].setdefault(r["service"], {"calls": 0, "errors": 0, "audio_seconds": 0.0, "chars": 0})
        s["calls"] += 1
        s["errors"] += 0 if r.get("ok") else 1
        s["audio_seconds"] += r.get("audio_seconds") or 0.0
        s["chars"] += r.get("chars") or 0
    return out
