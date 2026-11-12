"""Build a small SYNTHETIC dev set with Timbre, for developing the pipeline only.

Cost: 1 Timbre call per item. Transcription happens later in run_bench.py (3 Prisma calls
per item: clean / narrowband / noisy). So --n 12 costs 12 TTS + 36 STT calls.

  python scripts/build_synth_set.py --n 12            # dry run
  python scripts/build_synth_set.py --n 12 --run
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indicintentguard import ledger  # noqa: E402
from indicintentguard.config import DATA, get_settings  # noqa: E402
from indicintentguard.gnani import synthesize  # noqa: E402
from indicintentguard.templates import generate  # noqa: E402

VOICES = {"te-IN": ["Suhana", "Lavanya", "Varuni"], "hi-en": ["Poorvi"], "en-IN": ["Kaveri", "Pranav", "Girish"]}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    items = generate(args.n, seed=args.seed)
    s = get_settings()
    print(f"{len(items)} items -> {len(items)} Timbre calls now, {3 * len(items)} Prisma calls in run_bench.py")
    print(f"Ledger: {ledger.call_count()} used, cap {s.max_api_calls}")
    for it in items:
        print(f"  {it.id} [{it.category:<18} {it.style}] {it.tts_text}")
    if not args.run:
        print("\nDry run. Add --run to synthesize.")
        return

    raw_dir = DATA / "raw"
    labels = []
    for k, it in enumerate(items):
        voices = VOICES[it.tts_lang]
        voice = voices[k % len(voices)]
        try:
            r = synthesize(it.tts_text, language=it.tts_lang, voice=voice, model="timbre-v2.5")
        except ledger.BudgetExceeded as e:
            print("STOP:", e)
            break
        except Exception as e:
            print(f"  {it.id} ERROR {str(e)[:200]}")
            continue
        wav = raw_dir / f"{it.id}.wav"
        shutil.copy(r["path"], wav)
        labels.append({
            "id": it.id, "speaker": f"tts_{voice}", "split": "dev", "audio_file": wav.name,
            "language_code": it.prisma_lang, "reference_transcript": it.sheet, "action": it.action,
            "superseded": it.superseded, "correction_present": it.correction_present,
            "negation_present": it.negation_present, "risk": it.risk, "tags": it.tags + ["synthetic"],
        })
        print(f"  {it.id} ok ({voice})")
    out = DATA / "labels" / "synthetic_dev.jsonl"
    out.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in labels) + "\n", encoding="utf-8")
    print(f"Wrote {len(labels)} labels to {out}")


if __name__ == "__main__":
    main()
