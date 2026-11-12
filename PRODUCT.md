# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: contest judges for the Gnani AI Great India Internship, who mostly watch a 2–3 minute **screen recording** of the demo. They need to grasp the point quickly, at video resolution, without operating it themselves. Secondary: Gnani engineers who may run it locally.

## Product Purpose
IndicIntentGuard is a verification layer between Gnani Prisma (speech-to-text) and a voice agent's action. For each spoken instruction it decides whether to execute, ask a targeted spoken confirmation (via Gnani Timbre), or escalate, so callers mixing Telugu or Hindi with English, correcting themselves, or calling on noisy lines don't get the wrong amount or account executed. Success: a viewer sees, within ~10 seconds, a naive agent execute the wrong value and the guard catch it.

## Positioning
Works only from outside the model. Prisma exposes no confidence scores, so the guard builds its own evidence: correction structure, Prisma's own ITN-vs-literal disagreement from a single call, teen/ty confusability, bandwidth/SNR measured from the audio, and account context. Every decision is shown with its reasons.

## Operating Context
Local FastAPI demo (`app/`) at localhost:8000. Flow: record or pick a clip → Prisma transcript (+ literal) → B0 naive vs B3 guard decision → Timbre speaks a confirmation → caller answers by voice or with buttons → mock bank ledger. Cached clips cost no credits; live calls cost about 4 credits each out of 5,000.

## Capabilities and Constraints
- Decisions: accept, clarify (with the fields to confirm), escalate. Five systems: B0, B0+parse, B1, B2, B3.
- Transcripts may be Latin, Telugu or Devanagari script; prompts in English, Hinglish or Telugu.
- Mock execution only; not a certified safety system.
- No benchmark results on real speakers yet. Don't present the smoke-test numbers as findings.

## Brand Commitments
- Mention Gnani Prisma and Timbre by name as the models used. No Gnani logos or site imitation (not confirmed either way; default to neutral).
- Telugu and Devanagari text must render well.
- Must not look like the glowing dark-mode "AI dashboard" aesthetic.

## Evidence on Hand
Real Prisma outputs from the probe (`data/probe/probe_results.json`, `data/cache/prisma/`), including Prisma's own ITN slips ("rupees to" → "रुपये 2"). The three clips are Timbre-synthesised, so label them synthetic. No customers, testimonials or benchmark claims exist; don't invent any.

## Product Principles
1. Show the failure next to the fix. The comparison is the argument.
2. Every decision explains itself in plain words.
3. Honest about limits: synthetic clips are labelled, and assumptions are stated.
4. Readable on video: large, high-contrast, and with one thing happening at a time.
