"""Day-1 feasibility probe for Prisma (STT) and Timbre (TTS).

Answers, with as few credits as possible:
  1. Which fields does Prisma actually return? (any confidence / word timings / alternatives?)
  2. Does te-IN or en-IN handle Telugu-English code-mixed speech better? Which script comes back?
  3. How does it handle 8 kHz telephone audio? (run with --conditions)
  4. verbatim vs transcribe (ITN): how do spoken amounts come back?
  5. Latency, and - by comparing your dashboard balance before/after - credits per call.

Dry run by default: prints the planned calls and spends nothing. Add --run to call the APIs.

  python scripts/probe.py data/probe/*.wav
  python scripts/probe.py data/probe/*.wav --conditions --run
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indicintentguard import cache, ledger  # noqa: E402
from indicintentguard.audio import make_conditions  # noqa: E402
from indicintentguard.config import DATA, get_settings  # noqa: E402
from indicintentguard.extract import extract_amounts, find_correction_cues  # noqa: E402
from indicintentguard.gnani import synthesize, transcribe  # noqa: E402

TTS_PROBES = [
    ("en-IN", "Just to confirm, the amount is thirteen thousand rupees. Is that correct?"),
    ("te-IN", "మీరు చెప్పిన మొత్తం పదమూడు వేల రూపాయలు. సరియేనా?"),
]


def plan_stt(clips: list[Path], langs: list[str], formats: list[str], conditions: bool) -> list[tuple]:
    jobs = []
    for clip in clips:
        variants = {"original": clip}
        if conditions:
            variants.update(make_conditions(clip, DATA / "probe" / "conditions"))
            variants.pop("clean", None)  # "original" already covers the clean case
        for cond, path in variants.items():
            for lang in langs:
                for fmt in formats:
                    if cond != "original" and fmt != formats[0]:
                        continue  # only test format variations on the original clip
                    jobs.append((clip.stem, cond, path, lang, fmt))
    return jobs


def is_cached_stt(path: Path, lang: str, fmt: str) -> bool:
    params = {"language_code": lang, "format": fmt}
    return cache.path_for("prisma", cache.key_for(path.read_bytes(), params), "json").exists()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+", type=Path, help="3-5 short WAV/FLAC clips (<= 30 s each)")
    ap.add_argument("--langs", nargs="+", default=["te-IN", "en-IN"])
    ap.add_argument("--formats", nargs="+", default=["verbatim", "transcribe"])
    ap.add_argument("--conditions", action="store_true", help="also send 8 kHz narrowband + noisy versions")
    ap.add_argument("--no-tts", action="store_true")
    ap.add_argument("--run", action="store_true", help="actually call the APIs (spends credits)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

    s = get_settings()
    missing = [c for c in args.clips if not c.exists()]
    if missing:
        sys.exit(f"Missing clips: {missing}")

    jobs = plan_stt(args.clips, args.langs, args.formats, args.conditions)
    new_stt = sum(not is_cached_stt(p, l, f) for _, _, p, l, f in jobs)
    new_tts = 0 if args.no_tts else len(TTS_PROBES)
    used = ledger.call_count()

    print(f"Planned: {len(jobs)} Prisma calls ({new_stt} uncached) + {new_tts} Timbre calls (cached ones are free)")
    print(f"Ledger: {used} calls used so far, cap MAX_API_CALLS={s.max_api_calls}")
    if used + new_stt + new_tts > s.max_api_calls:
        print("WARNING: this run would exceed MAX_API_CALLS; it will stop at the cap.")
    if not args.run:
        for j in jobs:
            print(f"  STT  {j[0]:<20} {j[1]:<11} {j[3]:<6} {j[4]}")
        print("\nDry run only. Note your dashboard credit balance, then re-run with --run.")
        return
    if not s.api_key:
        sys.exit("GNANI_API_KEY is empty. Copy .env.example to .env and add your key.")

    results = []
    for clip, cond, path, lang, fmt in jobs:
        try:
            r = transcribe(path, lang, fmt)
            row = {"clip": clip, "condition": cond, "lang": lang, "format": fmt,
                   "transcript": r["transcript"], "response_fields": sorted(r["raw"].keys()),
                   "latency_ms": r["latency_ms"], "cached": r["cached"],
                   "amounts_parsed": extract_amounts(r["transcript"]),
                   "correction_cues": find_correction_cues(r["transcript"])}
        except ledger.BudgetExceeded as e:
            print(f"STOP: {e}")
            break
        except Exception as e:  # keep probing other configs; errors are findings too
            row = {"clip": clip, "condition": cond, "lang": lang, "format": fmt, "error": str(e)[:500]}
        results.append(row)
        print(json.dumps(row, ensure_ascii=False))

    tts_results = []
    if not args.no_tts:
        for lang, text in TTS_PROBES:
            try:
                r = synthesize(text, language=lang)
                tts_results.append({"lang": lang, "text": text, "path": r["path"],
                                    "latency_ms": r["latency_ms"], "cached": r["cached"]})
            except ledger.BudgetExceeded as e:
                print(f"STOP: {e}")
                break
            except Exception as e:
                tts_results.append({"lang": lang, "text": text, "error": str(e)[:500]})
            print(json.dumps(tts_results[-1], ensure_ascii=False))

    out = DATA / "probe" / "probe_results.json"
    out.write_text(json.dumps({"stt": results, "tts": tts_results, "ledger": ledger.summary()},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {out}")
    print("Ledger:", json.dumps(ledger.summary()))
    print("Now check your dashboard balance: (before - after) / calls = credits per call.")


if __name__ == "__main__":
    main()
