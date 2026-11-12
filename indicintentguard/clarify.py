"""Targeted clarification: ask only about the risky field, in the caller's language,
with the number said both as words and digit-by-digit (disambiguates thirteen vs thirty).
Then interpret the caller's spoken yes / no / new value.
"""
from .extract import parse
from .numbers import _ALIASES, parse_numbers, spell_amount, spell_digits
from .schemas import Action

_SCRIPT_FORM = {  # first Telugu / Devanagari transliteration of each English number word
    "te-IN": {c: next((f for f in forms if "ఀ" <= f[0] <= "౿"), c) for c, forms in _ALIASES.items()},
    "hi-IN": {c: next((f for f in forms if "ऀ" <= f[0] <= "ॿ"), c) for c, forms in _ALIASES.items()},
}

TEMPLATES = {
    "en-IN": {
        "amount": "Just to confirm, {amount} rupees, that is {digits}. Shall I go ahead?",
        "account_id": "Just to confirm, the account ending {acct}. Is that correct?",
        "both": "Just to confirm, {amount} rupees, that is {digits}, to the account ending {acct}. Shall I go ahead?",
        "missing": "Sorry, I did not catch the amount. How much should I {verb}?",
    },
    "hi-en": {
        "amount": "Confirm kar rahi hoon, {amount} rupees, yaani {digits}. Kya main aage badhoon?",
        "account_id": "Confirm kar rahi hoon, account ending {acct}. Sahi hai?",
        "both": "Confirm kar rahi hoon, {amount} rupees, yaani {digits}, account ending {acct}. Aage badhoon?",
        "missing": "Maaf kijiye, amount samajh nahi aaya. Kitna {verb} karna hai?",
    },
    "te-IN": {
        "amount": "నిర్ధారించడానికి, {amount} రూపాయలు, అంటే {digits}. ముందుకు వెళ్ళమంటారా?",
        "account_id": "నిర్ధారించడానికి, అకౌంట్ ఎండింగ్ {acct}. సరైనదేనా?",
        "both": "నిర్ధారించడానికి, {amount} రూపాయలు, అంటే {digits}, అకౌంట్ ఎండింగ్ {acct}. ముందుకు వెళ్ళమంటారా?",
        "missing": "క్షమించండి, మొత్తం అర్థం కాలేదు. ఎంత {verb} చేయాలి?",
    },
}
VOICES = {"en-IN": ("en-IN", "Kaveri", "timbre-v2.5"),
          "hi-en": ("hi-en", "Poorvi", "timbre-v2.5"),
          "te-IN": ("te-IN", "Suhana", "timbre-v2.5")}

YES = {"yes", "yeah", "yep", "haan", "han", "ha", "haa", "हाँ", "हां", "हा", "ji", "जी", "avunu", "అవును", "sare",
       "సరే", "ok", "okay", "ओके", "ఓకే", "correct", "sahi", "सही", "theek", "ठीक", "confirm", "go", "aage"}
NO = {"no", "nahi", "nahin", "नहीं", "नही", "kaadu", "kadu", "కాదు", "ledu", "లేదు", "wrong", "galat", "गलत",
      "vaddu", "వద్దు", "cancel", "mat"}


def _say(words: str, lang: str) -> str:
    table = _SCRIPT_FORM.get("te-IN" if lang == "te-IN" else "")
    return " ".join(table.get(w, w) for w in words.split()) if table else words


def build_prompt(action: Action | None, fields: list[str], lang: str = "en-IN") -> str:
    t = TEMPLATES.get(lang, TEMPLATES["en-IN"])
    if action is None or ("amount" in fields and action.amount is None):
        verb = "transfer" if action is None or action.intent.value == "transfer" else "request"
        return t["missing"].format(verb=verb)
    amount = _say(spell_amount(action.amount), lang) if action.amount is not None else ""
    digits = _say(spell_digits(str(action.amount)), lang) if action.amount is not None else ""
    acct = _say(spell_digits(action.account_id), lang) if action.account_id else ""
    if "amount" in fields and "account_id" in fields and acct:
        return t["both"].format(amount=amount, digits=digits, acct=acct)
    if "account_id" in fields and acct:
        return t["account_id"].format(acct=acct)
    return t["amount"].format(amount=amount, digits=digits)


def interpret_reply(text: str, pending: Action) -> tuple[str, Action | None]:
    """-> ("confirmed" | "corrected" | "rejected" | "unclear", resulting action)."""
    toks = set(parse_numbers(text)[0])
    p = parse(text, naive=False)
    if p.action and p.action.amount is not None and p.action.amount != pending.amount:
        return "corrected", pending.model_copy(update={"amount": p.action.amount})
    if p.action and p.action.account_id and p.action.account_id != pending.account_id:
        return "corrected", pending.model_copy(update={"account_id": p.action.account_id})
    if toks & NO:
        return "rejected", None
    if toks & YES:
        return "confirmed", pending
    return "unclear", None
