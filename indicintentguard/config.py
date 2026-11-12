from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE_DIR = DATA / "cache"
LEDGER_PATH = DATA / "ledger.jsonl"

load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    api_key: str
    prisma_url: str
    timbre_url: str
    max_api_calls: int
    timbre_model: str
    timbre_voice: str


def get_settings() -> Settings:
    return Settings(
        api_key=os.getenv("GNANI_API_KEY", "").strip(),
        prisma_url=os.getenv("PRISMA_URL", "https://api.vachana.ai/stt/v3"),
        timbre_url=os.getenv("TIMBRE_URL", "https://api.vachana.ai/api/v1/tts/inference"),
        max_api_calls=int(os.getenv("MAX_API_CALLS", "40")),
        timbre_model=os.getenv("TIMBRE_MODEL", "timbre-v2.5"),
        timbre_voice=os.getenv("TIMBRE_VOICE", "Kaveri"),
    )
