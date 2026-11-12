"""Offline tests: no API key, no credits. Transcripts below are real Prisma outputs from the probe."""
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from indicintentguard import ledger
from indicintentguard.audio import make_conditions
from indicintentguard.clarify import build_prompt, interpret_reply
from indicintentguard.evidence import Observation, audio_stats, compute
from indicintentguard.extract import parse
from indicintentguard.metrics import action_correct, summarize, wilson
from indicintentguard.numbers import parse_numbers, spell_amount
from indicintentguard.policies import POLICIES
from indicintentguard.risk import RiskModel
from indicintentguard.schemas import Action, Decision, Sample
from indicintentguard.templates import generate

ROOT = Path(__file__).resolve().parent.parent

# (transcript, literal, expected final amount, expected account) — real Prisma v2.5 outputs
REAL = [
    ("30,000 nahi 13,000 ka transfer karo", "thirty thousand nahi thirteen thousand ka transfer karo", 13000, None),
    ("30,000 kadu 13,000 transfer k", "thirty thousand kadu thirteen thousand transfer k", 13000, None),
    ("30 తౌసండ్ కాదు థర్టీన్ తౌసండ్ ట్రాన్స్ఫర్ చేయండి", None, 13000, None),
    ("30 थाउज़ंड कादू 13 थाउज़ंड ट्रांसफर चाहिए", None, 13000, None),
    ("please transfer ₹15,000 to account ending 4567",
     "please transfer fifteen thousand rupees to account ending four five six seven", 15000, "4567"),
    ("प्लीज़ ट्रांस्फर 15 थाउज़ंड रुपये 2 अकाउन्ट एंडिंग 4567", None, 15000, "4567"),
    ("ప్లీజ్ ట్రాన్స్ ఫర్ ఫిఫ్టీన్ థౌజండ్ రూపాయలు టు అకౌంట్ ఎండింగ్ ఫోర్ ఫైవ్ సిక్స్ సెవెన్", None, 15000, "4567"),
]


@pytest.mark.parametrize("text,literal,amount,acct", REAL)
def test_correction_aware_parse_on_real_prisma_output(text, literal, amount, acct):
    a = parse(text).action
    assert a.amount == amount and a.account_id == acct and a.intent.value == "transfer"


def test_naive_parse_takes_superseded_value():
    assert parse("30,000 nahi 13,000 ka transfer karo", naive=True).action.amount == 30000


def test_numbers():
    vals = lambda t: [s.value for s in parse_numbers(t)[1]]
    assert vals("two lakh fifty thousand") == [250000]
    assert vals("1,50,000") == [150000]
    assert vals("one hundred and five") == [105]
    spans = parse_numbers("account ending four five six seven")[1]
    assert spans[0].kind == "digits" and spans[0].digits == "4567"
    assert spell_amount(1250000) == "twelve lakh fifty thousand"


@pytest.mark.parametrize("text,literal,amount,acct", REAL)
def test_guard_never_executes_wrong_amount(text, literal, amount, acct):
    out = POLICIES["B3_guard"](Observation(text, literal))
    assert out.decision != Decision.accept or out.action.amount == amount


def test_b0_executes_the_wrong_amount():
    out = POLICIES["B0_direct"](Observation(REAL[0][0], REAL[0][1]))
    assert out.decision == Decision.accept and out.action.amount == 30000


def test_guard_accepts_clean_request_but_b1_b2_interrupt():
    obs = Observation(REAL[4][0], REAL[4][1])
    assert POLICIES["B3_guard"](obs).decision == Decision.accept
    assert POLICIES["B1_always_confirm"](obs).decision == Decision.clarify


def test_itn_literal_mismatch_is_evidence():
    _, f, _ = compute(Observation("transfer ₹30,000", "transfer thirteen thousand rupees"))
    assert f["itn_literal_mismatch"] == 1


def test_context_violation_escalates():
    obs = Observation(REAL[4][0], REAL[4][1], ctx={"known_accounts": ["XXXX1111"]})
    assert POLICIES["B3_guard"](obs).decision == Decision.escalate


def test_clarify_prompt_and_reply():
    a = Action(intent="transfer", amount=13000)
    assert "one three zero zero zero" in build_prompt(a, ["amount"], "en-IN")
    assert "థర్టీన్" in build_prompt(a, ["amount"], "te-IN")
    assert interpret_reply("haan", a)[0] == "confirmed"
    assert interpret_reply("ledu", a)[0] == "rejected"
    status, new = interpret_reply("no, thirty thousand", a)
    assert status == "corrected" and new.amount == 30000


def test_templates_and_labels_validate():
    for it in generate(30):
        s = Sample(id=it.id, speaker="x", split="dev", audio_file="x.wav", language_code=it.prisma_lang,
                   reference_transcript=it.sheet, action=it.action, risk=it.risk)
        # the parser must recover the gold action from the script text itself
        assert action_correct(parse(it.sheet).action, s.action.model_dump(exclude_none=True)), it.sheet
    lines = (ROOT / "data/labels/example_labels.jsonl").read_text(encoding="utf-8").splitlines()
    assert all(Sample(**json.loads(l)) for l in lines if l.strip())


def test_metrics():
    gold = {"intent": "transfer", "amount": 13000}
    rows = [{"out": POLICIES["B0_direct"](Observation(REAL[0][0])), "gold": gold, "risk": "high"},
            {"out": POLICIES["B3_guard"](Observation(REAL[0][0], REAL[0][1])), "gold": gold, "risk": "high"}]
    m = summarize(rows, RiskModel().error_cost)
    assert m["unsafe_execution"]["k"] == 1
    lo, hi = wilson(0, 10)
    assert lo == 0 and 0.2 < hi < 0.35


def test_risk_fit_moves_toward_data():
    X = [dict.fromkeys(RiskModel().w, 0.0) | {"confusable_amount": 1.0} for _ in range(40)]
    m = RiskModel().fit(X, [1] * 40)
    assert m.w["confusable_amount"] > RiskModel().w["confusable_amount"]


def test_conditions_and_audio_stats(tmp_path):
    sr = 16000
    rng = np.random.default_rng(0)
    sf.write(tmp_path / "x.wav", 0.1 * rng.standard_normal(sr * 2), sr)  # broadband
    paths = make_conditions(tmp_path / "x.wav", tmp_path / "out")
    assert sf.info(str(paths["narrowband"])).samplerate == 8000
    assert audio_stats(paths["clean"])["hf_energy_db"] > -45
    assert audio_stats(paths["narrowband"])["hf_energy_db"] < -45


def test_budget_guard(tmp_path):
    p = tmp_path / "ledger.jsonl"
    ledger.record({"service": "prisma", "ok": True, "audio_seconds": 3.0}, p)
    ledger.check_budget(2, p)
    ledger.record({"service": "timbre", "ok": True, "chars": 40}, p)
    with pytest.raises(ledger.BudgetExceeded):
        ledger.check_budget(2, p)
