# IndicIntentGuard

A risk-aware check that sits between **Gnani Prisma** (speech-to-text) and whatever action a voice agent takes. For every spoken instruction it decides whether to **execute**, **ask a targeted confirmation** (spoken by **Gnani Timbre**), or **escalate to a human**. The goal is that callers mixing Telugu or Hindi with English, correcting themselves mid-sentence, or calling on a noisy phone line don't end up with the wrong amount or account getting executed.

Built for the Gnani AI Great India Internship (deadline 10 Nov 2026, 11:59 PM IST).

> *"Thirty thousand kaadu, thirteen thousand transfer cheyyandi."*
> **Without a guard:** executes ₹30,000. **IndicIntentGuard:** keeps ₹13,000, sees the correction, the teen/ty risk and the cut-off ending, and asks *"thirteen thousand rupees, that is one three zero zero zero. Shall I go ahead?"*

## Quick start

```bash
pip install -r requirements.txt
copy .env.example .env               # put GNANI_API_KEY in .env
pytest                               # 26 offline tests, no credits
python -m uvicorn app.server:app --port 8000   # demo at http://localhost:8000
```

## What the probe found (27 Oct 2026, Prisma v2.5)

- **No confidence scores.** Not in REST, not in the WebSocket API, and no word timings or n-best lists. Any guard has to work from the outside, using what Prisma does return.
- **One call gives you two views.** With `format=transcribe`, a single call returns both `transcript` (with numbers written as digits) and `output.literal` (the words as spoken). If the two disagree, that's a free consistency check.
- **`en-IN` handles code-mixed speech best**, including Telugu-English: it returns Latin script with correct numbers. `te-IN` and `hi-IN` return English words in Telugu or Devanagari script.
- **Number conversion errors seen in Prisma itself:** `hi-IN` turned "rupees **to** account" into "रुपये **2** अकाउन्ट". `te-IN` converted "thirty" to 30 but left "thirteen" as a word.
- Prisma's server-side processing is about 140 ms. A full round trip from here is about 0.9–1.5 s.

## How B3 decides

Since Prisma exposes no confidence, every signal comes from evidence available outside the model ([evidence.py](indicintentguard/evidence.py)):

| Evidence | Source |
|---|---|
| Self-correction / negation structure (*nahi, kaadu, कादू, sorry, matlab, ante…*) | transcript |
| Several values with no clear correction, or only a negated value | transcript |
| ITN `transcript` vs `output.literal` disagree on a field | same Prisma call |
| Teen/ty confusable amounts (thirteen ↔ thirty) | literal words |
| Cut-off utterance, too few words for the audio length | transcript + audio |
| Telephone bandwidth, low SNR | the audio itself |
| Amount over the limit, account not the caller's | application context |

`P(wrong) = sigmoid(b + w·f)` ([risk.py](indicintentguard/risk.py)). It asks for confirmation when `P × C_error(risk tier) > C_clarify`. Irreversible actions always get confirmed, and context violations escalate. The weights start as hand-set priors, and `--fit dev` refines them on dev data with L2 regularisation that pulls them back toward the prior.

The confirmation is targeted: it asks only about the risky field, and says the number both as words and as digits, which separates *thirteen* from *thirty*. The caller's spoken *haan / avunu / no, thirty thousand* is transcribed by Prisma and interpreted by [clarify.py](indicintentguard/clarify.py).

## Experiment

| System | Description |
|---|---|
| B0 | Direct execution with naive extraction (the first value wins) |
| B0+parse | Direct execution with correction-aware extraction. An ablation that isolates the parser's contribution |
| B1 | Always confirm |
| B2 | Rule-based guard: correction keywords, multiple numbers, missing amount, amount ≥ ₹50k |
| B3 | IndicIntentGuard |

Metrics ([metrics.py](indicintentguard/metrics.py)), each reported with a Wilson 95% CI: field accuracy, unsafe execution rate, selective risk, clarification rate, unnecessary clarifications, error recall, and expected cost per call.

### Data workflow

```bash
# 1. Real speakers (the headline evidence): make a script sheet + gold labels
python scripts/make_recording_sheet.py --speakers s01 s02 s03 --per-speaker 20 --test s03
#    -> data/labels/recording_sheet.csv (what to read), data/labels/real.jsonl (gold)
#    Record each line as WAV into data/raw/, then check each label against what was actually said.

# 2. Optional synthetic dev set via Timbre (pipeline development only)
python scripts/build_synth_set.py --n 12            # dry run shows texts + call count
python scripts/build_synth_set.py --n 12 --run

# 3. Benchmark: transcribes clean / 8 kHz narrowband / noisy versions (cached), runs B0-B3
python scripts/run_bench.py --labels data/labels/real.jsonl --fit dev --eval test --run
#    -> data/results/report.md, results.json, per_item.csv
```

## Saving credits (5,000 total)

- Every Prisma and Timbre response is cached by a hash of the audio plus request parameters, so the same request is never paid for twice.
- Every real call is logged in `data/ledger.jsonl`. `MAX_API_CALLS` in `.env` is a hard stop.
- One `transcribe` call per clip and condition provides both the ITN and literal text, and every policy reuses it.
- Cost of the benchmark: 60 real clips × 3 conditions = 180 Prisma calls. The demo's Timbre prompts are cached once spoken.

## Layout

| Path | What |
|---|---|
| `indicintentguard/gnani/` | Prisma and Timbre clients (cache, ledger, budget guard) |
| `indicintentguard/numbers.py` | Number parsing for Latin, Telugu and Devanagari script, native Hindi and Telugu number words, digit strings, teen/ty pairs |
| `indicintentguard/extract.py` | Correction-aware action extraction |
| `indicintentguard/evidence.py` | Evidence features, plus bandwidth and SNR from audio |
| `indicintentguard/risk.py` | Calibrated risk model and cost-sensitive decision rule |
| `indicintentguard/policies.py` | B0, B0+parse, B1, B2, B3 |
| `indicintentguard/clarify.py` | Targeted confirmation prompts (en, Hinglish, Telugu) and reply interpretation |
| `indicintentguard/templates.py` | Utterance templates with gold actions |
| `app/` | FastAPI demo: mic → Prisma → guard → Timbre → reply → mock bank |
| `scripts/` | probe, recording sheet, synthetic set, conditions, benchmark |

## API reference (checked 2026-10-27)

- Prisma STT: `POST https://api.vachana.ai/stt/v3`, multipart, header `X-API-Key-ID`. [docs](https://docs.gnani.ai/api/STT/speech-to-text)
- Timbre TTS: `POST https://api.vachana.ai/api/v1/tts/inference`, JSON, returns raw audio. Voices used: Kaveri (en-IN), Poorvi (hi-en), Suhana (te-IN). [docs](https://docs.gnani.ai/api/TTS/tts-inference), [voices](https://docs.gnani.ai/api/TTS/available-voices)

## Limits

- Text and audio evidence can't catch a confident substitution that leaves no trace, for example a clean "thirteen" heard as a clean "thirty" with no correction. That's why high-risk and irreversible actions keep a confirmation floor.
- Synthetic (TTS) speech is only for developing the pipeline. Claims about callers need real, consenting speakers. Get written consent and keep `data/raw/` private (it's in `.gitignore`).
- This is a research prototype with mock execution. It is not a certified banking or healthcare safety system.
