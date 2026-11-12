"""Scoring a policy's decisions against gold actions, with Wilson 95% intervals.

A decision is scored on what would actually happen:
  accept   -> the extracted action executes; unsafe if it differs from gold
  clarify  -> a confirmation turn; we assume the caller's answer recovers the gold action
              (reported separately as an assumption, not measured)
  escalate -> handed to a human; nothing executes automatically
"""
import math

from .schemas import Action, Decision, PolicyOutput

ESCALATE_COST = 3.0


def action_correct(pred: Action | None, gold: dict) -> bool:
    if pred is None:
        return False
    if gold.get("intent") and gold["intent"] != "other" and pred.intent.value != gold["intent"]:
        return False
    for k in ("amount", "account_id", "date", "name"):
        if k in gold and gold[k] is not None and getattr(pred, k) != gold[k]:
            return False
    return True


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def summarize(rows: list[dict], error_cost: dict[str, float]) -> dict:
    """rows: {"out": PolicyOutput, "gold": dict, "risk": str}"""
    n = len(rows)
    acc = [r for r in rows if r["out"].decision == Decision.accept]
    clar = [r for r in rows if r["out"].decision == Decision.clarify]
    esc = [r for r in rows if r["out"].decision == Decision.escalate]
    correct = [action_correct(r["out"].action, r["gold"]) for r in rows]
    unsafe = sum(1 for r in acc if not action_correct(r["out"].action, r["gold"]))
    wrong = n - sum(correct)
    caught = sum(1 for r, c in zip(rows, correct) if not c and r["out"].decision != Decision.accept)
    unnecessary = sum(1 for r, c in zip(rows, correct) if c and r["out"].decision == Decision.clarify)
    cost = (sum(error_cost.get(r["risk"], 10.0) for r in acc if not action_correct(r["out"].action, r["gold"]))
            + len(clar) * 1.0 + len(esc) * ESCALATE_COST)

    def rate(k, d):
        lo, hi = wilson(k, d)
        return {"k": k, "n": d, "rate": (k / d) if d else None, "ci95": [round(lo, 3), round(hi, 3)]}

    return {
        "n": n,
        "extraction_accuracy": rate(sum(correct), n),
        "unsafe_execution": rate(unsafe, n),
        "selective_risk": rate(unsafe, len(acc)),
        "clarification_rate": rate(len(clar), n),
        "escalation_rate": rate(len(esc), n),
        "error_recall": rate(caught, wrong),
        "unnecessary_clarification": rate(unnecessary, sum(correct)),
        "expected_cost_per_call": round(cost / n, 3) if n else None,
    }
