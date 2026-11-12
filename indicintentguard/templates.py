"""Utterance templates for IndicActionBench.

Each item has a gold *action* plus three renderings:
  sheet    : what a human speaker reads (romanized; Telugu-English, Hinglish or English)
  tts_text : what Timbre is given for the synthetic dev set (script matches the voice)
  lang     : Prisma language_code to send (en-IN handles code-mixed speech best, per the probe)

Synthetic speech is only for developing the pipeline. Headline results must come from
real, consenting human speakers reading `sheet` (scripts/make_recording_sheet.py).
"""
import random
from dataclasses import dataclass

from .clarify import _SCRIPT_FORM
from .numbers import spell_amount, spell_digits

# (correct, misheard-pair) amounts: teen/ty confusables are deliberately over-represented.
AMOUNTS = [13000, 14000, 15000, 16000, 17000, 18000, 19000, 30000, 40000, 50000, 60000, 70000,
           2500, 7500, 12000, 25000, 45000, 150000, 1300, 1900]
WRONG_FOR = {13000: 30000, 14000: 40000, 15000: 50000, 16000: 60000, 17000: 70000, 18000: 80000,
             19000: 90000, 30000: 13000, 40000: 14000, 50000: 15000, 60000: 16000, 70000: 17000,
             1300: 3000, 1900: 9000}


@dataclass
class Item:
    id: str
    category: str
    style: str               # "te-en" | "hi-en" | "en"
    sheet: str
    tts_text: str
    tts_lang: str
    prisma_lang: str
    action: dict
    superseded: dict
    correction_present: bool
    negation_present: bool
    risk: str
    tags: list


def _te(words: str) -> str:
    return " ".join(_SCRIPT_FORM["te-IN"].get(w, w) for w in words.split())


PHRASES = {
    # style: transfer, to_account, neg, sorry, rupees, loan, appointment
    "te-en": {"transfer": ("transfer cheyyandi", "ట్రాన్స్ఫర్ చేయండి"), "acct": ("account ending", "అకౌంట్ ఎండింగ్"),
              "ki": ("ki", "కి"), "neg": ("kaadu", "కాదు"), "sorry": ("sorry", "సారీ"), "rs": ("rupees", "రూపాయలు"),
              "loan": ("loan request kaavali", "లోన్ రిక్వెస్ట్ కావాలి"),
              "appt": ("appointment book cheyyandi", "అపాయింట్మెంట్ బుక్ చేయండి")},
    "hi-en": {"transfer": ("transfer karo", "transfer karo"), "acct": ("account ending", "account ending"),
              "ki": ("mein", "mein"), "neg": ("nahi", "nahi"), "sorry": ("sorry", "sorry"), "rs": ("rupees", "rupees"),
              "loan": ("ka loan request chahiye", "ka loan request chahiye"),
              "appt": ("appointment book karo", "appointment book karo")},
    "en": {"transfer": ("transfer", "transfer"), "acct": ("account ending", "account ending"), "ki": ("to", "to"),
           "neg": ("no", "no"), "sorry": ("sorry", "sorry"), "rs": ("rupees", "rupees"),
           "loan": ("loan request please", "loan request please"),
           "appt": ("book an appointment", "book an appointment")},
}
TTS_LANG = {"te-en": "te-IN", "hi-en": "hi-en", "en": "en-IN"}


def _amt(n: int, style: str, tts: bool) -> str:
    w = spell_amount(n)
    return _te(w) if (tts and style == "te-en") else w


def _acct(d: str, style: str, tts: bool) -> str:
    w = spell_digits(d)
    return _te(w) if (tts and style == "te-en") else w


def render(category: str, style: str, amount: int, acct: str, wrong: int | None, wrong_acct: str | None,
           tts: bool) -> str:
    P = {k: v[1 if tts else 0] for k, v in PHRASES[style].items()}
    A, W = _amt(amount, style, tts), (_amt(wrong, style, tts) if wrong else "")
    C, WC = _acct(acct, style, tts), (_acct(wrong_acct, style, tts) if wrong_acct else "")
    en = style == "en"
    if category == "control":
        return (f"{P['transfer']} {A} {P['rs']} {P['ki']} {P['acct']} {C}" if en
                else f"{P['acct']} {C} {P['ki']} {A} {P['rs']} {P['transfer']}")
    if category == "neg_correction":
        return (f"transfer not {W}, {A} {P['rs']} {P['ki']} {P['acct']} {C}" if en
                else f"{W} {P['neg']}, {A} {P['rs']} {P['acct']} {C} {P['ki']} {P['transfer']}")
    if category == "repair_correction":
        return (f"{P['transfer']} {W}, {P['sorry']}, {A} {P['rs']} {P['ki']} {P['acct']} {C}" if en
                else f"{P['acct']} {C} {P['ki']} {W}, {P['sorry']}, {A} {P['rs']} {P['transfer']}")
    if category == "account_correction":
        return (f"{P['transfer']} {A} {P['rs']} {P['ki']} {P['acct']} {WC}, {P['sorry']}, {C}" if en
                else f"{A} {P['rs']} {P['acct']} {WC} {P['neg']}, {C} {P['ki']} {P['transfer']}")
    if category == "loan":
        return f"{A} {P['rs']} {P['loan']}" if not en else f"{P['loan']} for {A} {P['rs']}"
    if category == "schedule":
        return P["appt"]
    raise ValueError(category)


CATEGORIES = ["control", "neg_correction", "repair_correction", "account_correction", "loan", "schedule"]
CATEGORY_WEIGHTS = [4, 3, 2, 2, 2, 1]


def generate(n: int, seed: int = 7, styles=("te-en", "hi-en", "en")) -> list[Item]:
    rng = random.Random(seed)
    items = []
    for i in range(n):
        style = styles[i % len(styles)]
        cat = rng.choices(CATEGORIES, CATEGORY_WEIGHTS)[0]
        amount = rng.choice(AMOUNTS if cat not in ("neg_correction", "repair_correction") else list(WRONG_FOR))
        acct = f"{rng.randint(1000, 9999)}"
        wrong = WRONG_FOR.get(amount) if cat in ("neg_correction", "repair_correction") else None
        wrong_acct = f"{rng.randint(1000, 9999)}" if cat == "account_correction" else None
        intent = {"loan": "create_request", "schedule": "schedule"}.get(cat, "transfer")
        action = {"intent": intent}
        if cat != "schedule":
            action["amount"] = amount
        if cat not in ("loan", "schedule"):
            action["account_id"] = acct
        sup = {}
        if wrong:
            sup["amount"] = wrong
        if wrong_acct:
            sup["account_id"] = wrong_acct
        items.append(Item(
            id=f"syn_{i:03d}", category=cat, style=style,
            sheet=render(cat, style, amount, acct, wrong, wrong_acct, tts=False),
            tts_text=render(cat, style, amount, acct, wrong, wrong_acct, tts=True),
            tts_lang=TTS_LANG[style], prisma_lang="en-IN", action=action, superseded=sup,
            correction_present=bool(sup), negation_present=cat in ("neg_correction", "account_correction"),
            risk={"transfer": "high", "create_request": "medium", "schedule": "low"}[intent],
            tags=[cat, style] + (["confusable"] if any(w in spell_amount(amount) for w in
                                                       ("teen", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")) else []),
        ))
    return items
