"""Action extraction from Prisma transcripts (Latin, Telugu or Devanagari script).

Two modes:
  naive=True  : first value wins. What a plain "transcript -> slot filler" does, and
                exactly what breaks on "thirty thousand nahi, thirteen thousand".
  naive=False : correction-aware. Finds repair/negation cues between values and keeps
                the final intended value, recording the superseded one.
"""
import re
from dataclasses import dataclass, field

from .numbers import NumberSpan, parse_numbers
from .schemas import Action, Intent

# Negation that follows the rejected value: "thirty thousand NAHI", "thirty thousand KAADU".
NEGATION = {"no", "not", "nahi", "nahin", "nai", "नहीं", "नही", "kaadu", "kadu", "kaadhu", "కాదు", "कादू", "काडू", "कादु",
            "na", "ना", "mat", "मत", "vaddu", "వద్దు", "don't", "dont"}
# Repair markers between two values: "thirty, SORRY, thirteen".
REPAIR = {"sorry", "सॉरी", "సారీ", "actually", "matlab", "मतलब", "ante", "అంటే", "rather", "instead",
          "balki", "बल्कि", "wait", "ruko", "रुको", "aagandi", "ఆగండి", "correction", "change", "galti",
          "गलती", "mean"}
CUES = NEGATION | REPAIR

INTENT_KEYWORDS = {
    Intent.transfer: ["transfer", "ట్రాన్స్ఫర్", "ట్రాన్స్ఫర్", "ट्रांसफर", "ट्रांस्फर", "send", "bhej", "भेज",
                      "pampu", "పంపు", "pampandi", "pay", "पे", "పే"],
    Intent.cancel: ["cancel", "క్యాన్సల్", "कैंसल", "radd", "रद्द"],
    Intent.update_contact: ["update", "change number", "changeaddress", "అప్డేట్", "अपडेट"],
    Intent.schedule: ["schedule", "appointment", "book", "బుక్", "बुक", "అపాయింట్మెంట్"],
    Intent.create_request: ["request", "loan", "రిక్వెస్ట్", "रिक्वेस्ट", "లోన్", "लोन", "emi"],
}
ACCOUNT_WORDS = {"account", "a/c", "ac", "ending", "number", "id", "khata", "खाता", "అకౌంట్", "अकाउन्ट",
                 "अकाउंट", "एंडिंग", "ఎండింగ్", "ఖాతా", "नंबर", "నంబర్"}


@dataclass
class Parse:
    action: Action | None
    superseded: dict = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)   # correction_resolved, multiple_unresolved, negated_only, ...
    amount_span: NumberSpan | None = None
    tokens: list[str] = field(default_factory=list)
    cues: list[str] = field(default_factory=list)


def find_correction_cues(text: str) -> list[str]:
    toks = set(re.split(r"[\s,.;:!?।]+", text.lower()))
    found = sorted(toks & CUES)
    if "i mean" in text.lower():
        found.append("i mean")
    return found


def detect_intent(text: str) -> Intent | None:
    compact = re.sub(r"\s+", "", text.lower())
    for intent, kws in INTENT_KEYWORDS.items():
        if any(re.sub(r"\s+", "", k) in compact for k in kws):
            return intent
    return None


def _is_id(span: NumberSpan, toks: list[str]) -> bool:
    if span.kind == "digits":
        return True
    ctx = toks[max(0, span.start - 3):span.start]
    return span.kind != "amount" and any(t in ACCOUNT_WORDS for t in ctx)


def _resolve(cands: list[NumberSpan], toks: list[str], name: str, p: Parse) -> NumberSpan | None:
    if not cands:
        return None
    if len(cands) == 1:
        s = cands[0]
        after = toks[s.end:s.end + 2]
        if any(t in NEGATION for t in after) and not any(t in REPAIR for t in after):
            p.flags.append(f"{name}_negated_only")
        return s
    # Is there a cue right after / between consecutive values, or just before the first?
    last_cue_k = None
    for k in range(len(cands) - 1):
        gap = toks[cands[k].end:cands[k + 1].start]
        if any(t in CUES for t in gap):
            last_cue_k = k
    lead = toks[max(0, cands[0].start - 2):cands[0].start]
    if last_cue_k is None and any(t in NEGATION for t in lead):
        last_cue_k = 0  # "not thirty thousand, thirteen thousand"
    if last_cue_k is not None:
        final = cands[-1]
        p.superseded[name] = cands[last_cue_k].value if name == "amount" else cands[last_cue_k].digits
        p.flags.append(f"{name}_correction_resolved")
        return final
    p.flags.append(f"{name}_multiple_unresolved")
    return cands[-1]


def parse(text: str, naive: bool = False) -> Parse:
    toks, spans = parse_numbers(text)
    p = Parse(action=None, tokens=toks, cues=find_correction_cues(text))
    intent = detect_intent(text)

    ids = [s for s in spans if _is_id(s, toks)]
    amounts = [s for s in spans if s not in ids and (s.kind == "amount" or s.value >= 100)]

    if naive:
        amt = amounts[0] if amounts else None
        acc = ids[0] if ids else None
    else:
        amt = _resolve(amounts, toks, "amount", p)
        acc = _resolve(ids, toks, "account_id", p)

    if intent is None and amt is None and acc is None:
        p.flags.append("no_action")
        return p
    p.amount_span = amt
    p.action = Action(intent=intent or Intent.other,
                      amount=amt.value if amt else None,
                      account_id=acc.digits if acc else None)
    return p


def extract_action(text: str, naive: bool = True) -> Action | None:
    return parse(text, naive=naive).action


def extract_amounts(text: str) -> list[int]:
    return [s.value for s in parse_numbers(text)[1]]
