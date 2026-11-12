"""Make the script sheet for REAL speakers + matching gold labels.

Each speaker reads ~20 lines naturally (they may hesitate or rephrase; the annotator then
fixes `reference_transcript` and checks the gold action). Speakers are kept disjoint
across dev/test.

  python scripts/make_recording_sheet.py --speakers s01 s02 s03 --per-speaker 20 --test s03
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indicintentguard.config import DATA  # noqa: E402
from indicintentguard.templates import generate  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speakers", nargs="+", required=True)
    ap.add_argument("--per-speaker", type=int, default=20)
    ap.add_argument("--test", nargs="+", default=[], help="speakers held out for the test split")
    ap.add_argument("--styles", nargs="+", default=["te-en", "en", "hi-en"])
    args = ap.parse_args()

    sheet_path = DATA / "labels" / "recording_sheet.csv"
    labels_path = DATA / "labels" / "real.jsonl"
    rows, labels = [], []
    for si, spk in enumerate(args.speakers):
        for it in generate(args.per_speaker, seed=100 + si, styles=tuple(args.styles)):
            uid = f"{spk}_u{it.id[-3:]}"
            rows.append({"file_to_save_as": f"{uid}.wav", "read_this": it.sheet, "style": it.style,
                         "category": it.category})
            labels.append({
                "id": uid, "speaker": spk, "split": "test" if spk in args.test else "dev",
                "audio_file": f"{uid}.wav", "language_code": it.prisma_lang,
                "reference_transcript": it.sheet, "action": it.action, "superseded": it.superseded,
                "correction_present": it.correction_present, "negation_present": it.negation_present,
                "risk": it.risk, "tags": it.tags + ["real", "needs_annotation_check"],
            })
    with sheet_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    labels_path.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in labels) + "\n", encoding="utf-8")
    print(f"{len(rows)} lines -> {sheet_path}\nlabels -> {labels_path}")
    print("Record each line as WAV (16 kHz mono is ideal) into data/raw/ with the given filename.")


if __name__ == "__main__":
    main()
