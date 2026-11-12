"""Run IndicActionBench: transcribe (cached), apply every policy, score, write a report.

  python scripts/run_bench.py --labels data/labels/synthetic_dev.jsonl            # uses cache only
  python scripts/run_bench.py --labels data/labels/synthetic_dev.jsonl --run      # may call Prisma
  python scripts/run_bench.py --labels data/labels/real.jsonl --fit dev --eval test --run

--fit SPLIT  refines the B3 risk weights on that split (never the eval split) and saves them.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indicintentguard import ledger  # noqa: E402
from indicintentguard.audio import CONDITIONS, make_conditions  # noqa: E402
from indicintentguard.config import CACHE_DIR, DATA  # noqa: E402
from indicintentguard.evidence import Observation, compute  # noqa: E402
from indicintentguard.gnani.prisma import transcribe  # noqa: E402
from indicintentguard import cache  # noqa: E402
from indicintentguard.metrics import action_correct, summarize  # noqa: E402
from indicintentguard.policies import POLICIES  # noqa: E402
from indicintentguard.risk import RiskModel  # noqa: E402
from indicintentguard.schemas import Sample  # noqa: E402

FORMAT = "transcribe"   # one call returns both ITN `transcript` and `output.literal`
DEFAULT_CTX = {"max_amount": 200_000}
RESULTS = DATA / "results"


def observations(samples: list[Sample], conditions: list[str], run: bool) -> list[tuple[Sample, str, Observation]]:
    out = []
    for s in samples:
        src = DATA / "raw" / s.audio_file
        if not src.exists():
            print(f"  missing audio {src.name}; skipped")
            continue
        paths = make_conditions(src, DATA / "conditions")
        for cond in conditions:
            p = paths[cond]
            key = cache.key_for(p.read_bytes(), {"language_code": s.language_code, "format": FORMAT})
            if not run and not cache.path_for("prisma", key, "json", CACHE_DIR).exists():
                continue
            try:
                r = transcribe(p, s.language_code, FORMAT)
            except ledger.BudgetExceeded as e:
                print("STOP:", e)
                return out
            except Exception as e:
                print(f"  {p.name}: {str(e)[:200]}")
                continue
            out.append((s, cond, Observation.from_prisma(r, audio_path=str(p), ctx=dict(DEFAULT_CTX))))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", nargs="+", type=Path, required=True)
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    ap.add_argument("--fit", choices=["dev", "test"], default=None)
    ap.add_argument("--eval", choices=["dev", "test", "all"], default="all")
    ap.add_argument("--model", type=Path, default=DATA / "risk_model.json")
    ap.add_argument("--run", action="store_true", help="allow uncached Prisma calls (spends credits)")
    args = ap.parse_args()

    samples = [Sample(**json.loads(l)) for f in args.labels
               for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    obs = observations(samples, args.conditions, args.run)
    print(f"{len(obs)} observations from {len(samples)} samples; ledger {ledger.call_count()} calls")
    if not obs:
        sys.exit("Nothing to score (no cached transcripts). Re-run with --run.")

    model = RiskModel.load(args.model) if args.model.exists() and not args.fit else RiskModel()
    if args.fit:
        if args.fit == args.eval:
            sys.exit("Refusing to fit and evaluate on the same split.")
        fit_rows = [(s, o) for s, _, o in obs if s.split == args.fit]
        X = [compute(o)[1] for _, o in fit_rows]
        y = [0 if action_correct(compute(o)[0].action, s.action.model_dump(exclude_none=True)) else 1
             for s, o in fit_rows]
        model.fit(X, y)
        model.save(args.model)
        print(f"Fitted risk model on {len(X)} {args.fit} rows ({sum(y)} wrong) -> {args.model}")

    ev = [(s, c, o) for s, c, o in obs if args.eval == "all" or s.split == args.eval]
    RESULTS.mkdir(parents=True, exist_ok=True)
    per_item, report = [], {}
    by_policy: dict[str, dict[str, list]] = {name: {} for name in POLICIES}
    for s, cond, o in ev:
        gold = s.action.model_dump(exclude_none=True)
        for name, pol in POLICIES.items():
            out = pol(o, model)
            row = {"out": out, "gold": gold, "risk": s.risk}
            for key in ("all", cond, *[f"tag:{t}" for t in s.tags if t in
                                        ("control", "neg_correction", "repair_correction", "account_correction",
                                         "confusable")]):
                by_policy[name].setdefault(key, []).append(row)
            per_item.append({"id": s.id, "condition": cond, "policy": name, "decision": out.decision.value,
                             "pred": json.dumps(out.action.model_dump(exclude_none=True) if out.action else None),
                             "gold": json.dumps(gold), "correct": action_correct(out.action, gold),
                             "transcript": o.transcript, "reasons": " | ".join(out.reasons)})

    for name, groups in by_policy.items():
        report[name] = {k: summarize(v, model.error_cost) for k, v in groups.items()}

    (RESULTS / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (RESULTS / "per_item.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(per_item[0]))
        w.writeheader()
        w.writerows(per_item)

    lines = [f"# IndicActionBench results\n", f"Labels: {', '.join(str(p) for p in args.labels)}  ",
             f"Eval split: {args.eval} | observations: {len(ev)} | conditions: {', '.join(args.conditions)}\n",
             "| Policy | Field acc. | Unsafe exec. (95% CI) | Clarify rate | Unnecessary clarify | Error recall | Cost/call |",
             "|---|---|---|---|---|---|---|"]
    for name in POLICIES:
        m = report[name]["all"]
        f = lambda x: "-" if x["rate"] is None else f"{x['rate']:.1%}"
        lines.append(f"| {name} | {f(m['extraction_accuracy'])} | {f(m['unsafe_execution'])} "
                     f"[{m['unsafe_execution']['ci95'][0]:.0%}-{m['unsafe_execution']['ci95'][1]:.0%}] | "
                     f"{f(m['clarification_rate'])} | {f(m['unnecessary_clarification'])} | {f(m['error_recall'])} | "
                     f"{m['expected_cost_per_call']} |")
    lines.append("\nClarified items assume the caller's answer recovers the intended action (not measured here).")
    if any("synthetic" in s.tags for s, _, _ in ev):
        lines.append("\n**Synthetic (TTS) speech: pipeline-development numbers only, not evidence about real callers.**")
    (RESULTS / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {RESULTS / 'report.md'}, results.json, per_item.csv")


if __name__ == "__main__":
    main()
