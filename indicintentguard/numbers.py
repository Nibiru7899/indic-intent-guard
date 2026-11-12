"""Multilingual, multi-script number parsing for Prisma transcripts.

Prisma returns spoken English numbers in whatever script the language_code implies:
  en-IN : "thirty thousand"          te-IN : "థర్టీ థౌజండ్"          hi-IN : "थर्टी थाउज़ंड"
and ITN ("transcribe") output can mix digits and words: "30 థౌజండ్ ... థర్టీన్ థౌసండ్".
Every token is mapped to a canonical English number word, then one grammar parses all.
"""
import re
from dataclasses import dataclass, field

UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
SCALES = {"hundred": 100, "thousand": 1000, "lakh": 100_000, "crore": 10_000_000}

# Acoustically confusable pairs on narrowband phone audio (teen vs ty).
CONFUSABLE = {"thirteen": "thirty", "fourteen": "forty", "fifteen": "fifty", "sixteen": "sixty",
              "seventeen": "seventy", "eighteen": "eighty", "nineteen": "ninety"}
CONFUSABLE.update({v: k for k, v in CONFUSABLE.items()})

# Surface forms -> canonical word. Latin variants, Telugu-script and Devanagari-script
# transliterations of English numbers, and native Hindi / Telugu number words.
_ALIASES: dict[str, list[str]] = {
    "zero": ["జీరో", "ज़ीरो", "जीरो", "sunna", "shunya", "सुन्ना", "శూన్యం", "సున్నా"],
    "one": ["వన్", "वन", "ek", "एक", "okati", "ఒకటి"],
    "two": ["టూ", "टू", "do", "दो", "rendu", "రెండు"],
    "three": ["త్రీ", "थ्री", "teen", "तीन", "moodu", "mudu", "మూడు"],
    "four": ["ఫోర్", "फोर", "फ़ोर", "char", "chaar", "चार", "naalugu", "nalugu", "నాలుగు"],
    "five": ["ఫైవ్", "फाइव", "फ़ाइव", "paanch", "panch", "पांच", "पाँच", "aidu", "ఐదు"],
    "six": ["సిక్స్", "सिक्स", "chhah", "chhe", "छह", "छः", "aaru", "ఆరు"],
    "seven": ["సెవెన్", "सेवन", "saat", "सात", "edu", "eedu", "ఏడు"],
    "eight": ["ఎయిట్", "ఎయిత్", "एट", "aath", "आठ", "enimidi", "ఎనిమిది"],
    "nine": ["నైన్", "नाइन", "nau", "नौ", "tommidi", "తొమ్మిది"],
    "ten": ["టెన్", "टेन", "das", "दस", "padi", "పది"],
    "eleven": ["ఎలెవెన్", "इलेवन", "gyarah", "ग्यारह", "padakondu", "పదకొండు"],
    "twelve": ["ట్వెల్వ్", "ट्वेल्व", "barah", "बारह", "pannendu", "పన్నెండు"],
    "thirteen": ["థర్టీన్", "తర్టీన్", "थर्टीन", "terah", "tera", "तेरह", "padamudu", "padamoodu", "పదమూడు"],
    "fourteen": ["ఫోర్టీన్", "फोर्टीन", "chaudah", "चौदह", "padanalugu", "పధ్నాలుగు", "పద్నాలుగు"],
    "fifteen": ["ఫిఫ్టీన్", "फिफ्टीन", "pandrah", "पंद्रह", "padihenu", "పదిహేను"],
    "sixteen": ["సిక్స్టీన్", "सिक्सटीन", "solah", "सोलह", "padahaaru", "పదహారు"],
    "seventeen": ["సెవెంటీన్", "सेवनटीन", "satrah", "सत्रह", "padihedu", "పదిహేడు"],
    "eighteen": ["ఎయిటీన్", "एटीन", "atharah", "अठारह", "padhenimidi", "పద్దెనిమిది"],
    "nineteen": ["నైన్టీన్", "नाइनटीन", "unnis", "उन्नीस", "pandommidi", "పంతొమ్మిది"],
    "twenty": ["ట్వెంటీ", "ट्वेंटी", "bees", "बीस", "iravai", "ఇరవై"],
    "thirty": ["థర్టీ", "తర్టీ", "थर्टी", "tees", "तीस", "muppai", "ముప్పై"],
    "forty": ["ఫోర్టీ", "फोर्टी", "chalis", "chaalis", "चालीस", "nalabhai", "nalabai", "నలభై"],
    "fifty": ["ఫిఫ్టీ", "फिफ्टी", "pachas", "pachaas", "पचास", "yabhai", "yabai", "యాభై"],
    "sixty": ["సిక్స్టీ", "सिक्सटी", "saath", "साठ", "aravai", "అరవై"],
    "seventy": ["సెవెంటీ", "सेवनटी", "sattar", "सत्तर", "debbai", "డెబ్బై"],
    "eighty": ["ఎయిటీ", "एटी", "assi", "अस्सी", "enabhai", "ఎనభై"],
    "ninety": ["నైన్టీ", "नाइनटी", "nabbe", "नब्बे", "tombhai", "తొంభై"],
    "hundred": ["హండ్రెడ్", "हंड्रेड", "sau", "सौ", "vanda", "వంద", "వందల", "nooru", "నూరు"],
    "thousand": ["థౌజండ్", "థౌసండ్", "తౌసండ్", "తౌజండ్", "థౌజెండ్", "थाउज़ंड", "थाउजंड", "थाउसेंड",
                 "hazaar", "hazar", "हज़ार", "हजार", "veyyi", "vela", "వేయి", "వెయ్యి", "వేల", "thousands"],
    "lakh": ["lakhs", "lac", "lacs", "లాక్", "లాఖ్", "లక్ష", "లక్షల", "laksha", "लाख", "लैख"],
    "crore": ["crores", "కోటి", "కోట్ల", "koti", "करोड़", "करोड", "crore"],
}
WORD = {}
for canon, forms in _ALIASES.items():
    WORD[canon] = canon
    for f in forms:
        WORD[f.lower()] = canon

CURRENCY = {"rupees", "rupee", "rs", "inr", "₹", "rupaye", "rupaiye", "रुपये", "रुपए", "रूपीज़", "రూపాయలు",
            "రూపీస్", "రూపాయల", "rupayalu"}
CURRENCY_PREFIX = {"₹", "rs", "inr"}

TOKEN_RE = re.compile(r"₹|\d[\d,]*(?:\.\d+)?|[^\W\d_]+", re.UNICODE)


@dataclass
class NumberSpan:
    value: int
    start: int                  # token index
    end: int                    # exclusive
    kind: str                   # "amount" | "digits" (spelled digit string, e.g. an ID) | "number"
    words: list[str] = field(default_factory=list)  # canonical words used (for confusability)
    currency: bool = False

    @property
    def digits(self) -> str:
        return "".join(str(UNITS[w]) for w in self.words) if self.kind == "digits" else str(self.value)

    @property
    def confusable(self) -> bool:
        return any(w in CONFUSABLE for w in self.words)


def tokenize(text: str) -> list[str]:
    # Indic scripts: \w misses combining marks, so split on whitespace/punct and keep runs.
    toks = []
    text = re.sub(r"(?<=\d),(?=\d)", "", text.lower())  # "30,000" / "1,50,000" stay one number
    for raw in re.split(r"[\s,.;:!?।\"'()]+", text):
        if not raw:
            continue
        if raw.startswith("₹"):
            toks.append("₹")
            raw = raw[1:]
        m = re.fullmatch(r"(\d[\d,]*)([^\d].*)?", raw)
        if m:  # "15,000" or "30k"
            toks.append(m.group(1))
            if m.group(2):
                toks.append(m.group(2))
        elif raw:
            toks.append(raw)
    return toks


def _canon(tok: str) -> str | None:
    if tok in WORD:
        return WORD[tok]
    return None


def parse_numbers(text: str) -> tuple[list[str], list[NumberSpan]]:
    toks = tokenize(text)
    spans: list[NumberSpan] = []
    i = 0
    while i < len(toks):
        tok = toks[i]
        if re.fullmatch(r"\d[\d,]*", tok):
            start, val = i, int(tok.replace(",", ""))
            j, words = i + 1, []
            # ITN can emit "30 థౌజండ్" (digits + scale word in another script)
            while j < len(toks) and _canon(toks[j]) in SCALES:
                val *= SCALES[_canon(toks[j])]
                words.append(_canon(toks[j]))
                j += 1
            kind = "digits" if (len(tok) >= 4 and not words and tok.isdigit() and tok[0] == "0") else "number"
            spans.append(NumberSpan(val, start, j, kind, words))
            i = j
            continue
        c = _canon(tok)
        if c in UNITS or c in TENS or c in SCALES:
            start, words = i, []
            while i < len(toks):
                c2 = _canon(toks[i])
                if c2 in UNITS or c2 in TENS or c2 in SCALES:
                    words.append(c2)
                    i += 1
                elif toks[i] in ("and", "aur", "और") and words and i + 1 < len(toks) and _canon(toks[i + 1]) in UNITS | TENS:
                    i += 1
                else:
                    break
            spans.extend(_words_to_spans(words, start))
            continue
        i += 1
    # currency marking: "₹" before or "rupees" right after
    for s in spans:
        before = toks[s.start - 1] if s.start > 0 else ""
        after = toks[s.end] if s.end < len(toks) else ""
        s.currency = before in CURRENCY_PREFIX or after in CURRENCY
        if s.kind != "digits" and (s.currency or any(w in SCALES and w != "hundred" for w in s.words)):
            s.kind = "amount"
    return toks, spans


def _words_to_spans(words: list[str], start: int) -> list[NumberSpan]:
    # A run of >= 3 single-digit words with no scale is a spelled digit string ("four five six seven").
    if len(words) >= 3 and all(w in UNITS and UNITS[w] <= 9 for w in words):
        val = int("".join(str(UNITS[w]) for w in words))
        return [NumberSpan(val, start, start + len(words), "digits", words)]
    # "thirty thousand thirteen thousand" is two numbers, not 43000: a scale word that is not
    # smaller than the previous one starts a new number (Prisma output often has no commas).
    last_scale = None
    for k, w in enumerate(words):
        if w in SCALES and w != "hundred":
            if last_scale is not None and SCALES[w] >= last_scale:
                cut = k - 1
                while cut > 0 and words[cut - 1] not in SCALES:
                    cut -= 1
                cut = max(cut, 1)
                return _words_to_spans(words[:cut], start) + _words_to_spans(words[cut:], start + cut)
            last_scale = SCALES[w]
    total, cur = 0, 0
    for w in words:
        if w in UNITS:
            cur += UNITS[w]
        elif w in TENS:
            cur += TENS[w]
        elif w == "hundred":
            cur = max(cur, 1) * 100
        else:
            total += max(cur, 1) * SCALES[w]
            cur = 0
    return [NumberSpan(total + cur, start, start + len(words), "number", words)]


def confusable_alternative(span: NumberSpan) -> int | None:
    """The value you'd get if one teen/ty word were misheard as its pair (thirteen<->thirty)."""
    for k, w in enumerate(span.words):
        if w in CONFUSABLE:
            alt = span.words[:k] + [CONFUSABLE[w]] + span.words[k + 1:]
            return _words_to_spans(alt, 0)[0].value
    return None


_SPELL_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def spell_amount(n: int) -> str:
    """Indian-style English words for TTS: 1250000 -> 'twelve lakh fifty thousand'."""
    if n == 0:
        return "zero"
    parts = []
    for div, name in ((10_000_000, "crore"), (100_000, "lakh"), (1000, "thousand"), (100, "hundred")):
        q, n = divmod(n, div)
        if q:
            parts.append(f"{spell_amount(q)} {name}")
    if n:
        inv_units = {v: k for k, v in UNITS.items()}
        inv_tens = {v: k for k, v in TENS.items()}
        if n < 20:
            parts.append(inv_units[n])
        else:
            t, u = divmod(n, 10)
            parts.append(inv_tens[t * 10] + (f" {inv_units[u]}" if u else ""))
    return " ".join(parts)


def spell_digits(s: str) -> str:
    return " ".join(_SPELL_UNITS[int(c)] for c in s if c.isdigit())
