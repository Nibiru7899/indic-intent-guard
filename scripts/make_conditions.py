"""Render every recording in data/raw/ into clean / narrowband / noisy WAVs in data/conditions/.

Offline, costs no credits. Listen to the outputs before using them.
  python scripts/make_conditions.py --snr 10
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indicintentguard.audio import make_conditions  # noqa: E402
from indicintentguard.config import DATA  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snr", type=float, default=10.0)
    args = ap.parse_args()
    srcs = sorted(p for p in (DATA / "raw").iterdir() if p.suffix.lower() in {".wav", ".flac", ".ogg"})
    if not srcs:
        sys.exit("No recordings in data/raw/ (WAV/FLAC/OGG).")
    for src in srcs:
        paths = make_conditions(src, DATA / "conditions", snr_db=args.snr)
        print(src.name, "->", ", ".join(p.name for p in paths.values()))


if __name__ == "__main__":
    main()
