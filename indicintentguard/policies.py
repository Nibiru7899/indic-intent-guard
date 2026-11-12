"""The systems compared in the experiment. All run offline on cached Prisma results.

B0        direct execution, naive extraction (first value wins)
B0+parse  direct execution, correction-aware extraction   <- ablation: isolates the parser
B1        always confirm critical fields
B2        rule-based guard (keyword cues, multiple numbers, missing amount, large amount)
B3        IndicIntentGuard: correction-aware parse + black-box evidence + calibrated,
          cost-sensitive risk policy with targeted confirmation
"""
from typing import Callable

from .evidence import Observation, compute
from .extract import find_correction_cues, parse
from .risk import INTENT_RISK, RiskModel
from .schemas import Decision, PolicyOutput

B2_LARGE_AMOUNT = 50_000


def b0_direct(obs: Observation, model: RiskModel | None = None) -> PolicyOutput:
    return PolicyOutput(decision=Decision.accept, action=parse(obs.transcript, naive=True).action)


def b0_parse(obs: Observation, model: RiskModel | None = None) -> PolicyOutput:
    return PolicyOutput(decision=Decision.accept, action=parse(obs.transcript, naive=False).action)


def b1_always_confirm(obs: Observation, model: RiskModel | None = None) -> PolicyOutput:
    action = parse(obs.transcript, naive=True).action
    fields = list(action.critical()) if action else ["amount"]
    return PolicyOutput(decision=Decision.clarify, action=action, fields_to_confirm=fields or ["amount"],
                        reasons=["always_confirm"])


def b2_rules(obs: Observation, model: RiskModel | None = None) -> PolicyOutput:
    p = parse(obs.transcript, naive=True)
    action, reasons = p.action, []
    if action is None:
        return PolicyOutput(decision=Decision.clarify, action=None, reasons=["no_action_parsed"],
                            fields_to_confirm=["amount"])
    if find_correction_cues(obs.transcript):
        reasons.append("correction_cue")
    from .numbers import parse_numbers
    if len([s for s in parse_numbers(obs.transcript)[1] if s.value >= 100]) > 1:
        reasons.append("multiple_numbers")
    if action.intent.value in {"transfer", "create_request"} and action.amount is None:
        reasons.append("missing_amount")
    if action.amount and action.amount >= B2_LARGE_AMOUNT:
        reasons.append("large_amount")
    if reasons:
        return PolicyOutput(decision=Decision.clarify, action=action, reasons=reasons,
                            fields_to_confirm=list(action.critical()) or ["amount"])
    return PolicyOutput(decision=Decision.accept, action=action)


def b3_guard(obs: Observation, model: RiskModel | None = None) -> PolicyOutput:
    model = model or RiskModel()
    p, f, why = compute(obs)
    a = p.action
    tier = INTENT_RISK.get(a.intent.value if a else "other", "medium")
    tier = obs.ctx.get("risk", {}).get(a.intent.value if a else "other", tier)
    prob = model.prob(f)
    reasons = why + [f"P(wrong)={prob:.3f} vs threshold {model.threshold(tier) if tier != 'irreversible' else 0:.3f} ({tier} risk)"]

    fields = []
    if f["missing_field"] or any(f[k] for k in ("correction_resolved", "multiple_unresolved", "negated_only",
                                                 "confusable_amount", "truncated", "itn_literal_mismatch")):
        fields.append("amount")
    if a and a.account_id and (f["itn_literal_mismatch"] or "account_id_correction_resolved" in p.flags
                               or "account_id_multiple_unresolved" in p.flags):
        fields.append("account_id")
    if not fields and a:
        fields = list(a.critical()) or ["amount"]

    if f["context_violation"]:
        return PolicyOutput(decision=Decision.escalate, action=a, reasons=reasons, fields_to_confirm=fields)
    if tier == "irreversible" or a is None or f["missing_field"]:
        return PolicyOutput(decision=Decision.clarify, action=a, reasons=reasons, fields_to_confirm=fields)
    if prob > model.threshold(tier):
        return PolicyOutput(decision=Decision.clarify, action=a, reasons=reasons, fields_to_confirm=fields)
    return PolicyOutput(decision=Decision.accept, action=a, reasons=reasons)


POLICIES: dict[str, Callable[..., PolicyOutput]] = {
    "B0_direct": b0_direct,
    "B0+parse": b0_parse,
    "B1_always_confirm": b1_always_confirm,
    "B2_rules": b2_rules,
    "B3_guard": b3_guard,
}
