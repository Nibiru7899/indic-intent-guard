"""Content-addressed cache so the same audio + params is never sent to the API twice."""
import hashlib
import json
from pathlib import Path

from .config import CACHE_DIR


def key_for(payload: bytes, params: dict) -> str:
    h = hashlib.sha256(payload)
    h.update(json.dumps(params, sort_keys=True).encode())
    return h.hexdigest()[:32]


def path_for(service: str, key: str, ext: str, cache_dir: Path = CACHE_DIR) -> Path:
    return cache_dir / service / f"{key}.{ext}"
