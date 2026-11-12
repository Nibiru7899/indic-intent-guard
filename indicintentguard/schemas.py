"""Benchmark labels (IndicActionBench) and policy decisions.

The gold label is the user's final intended action, not just a transcript.
"""
from enum import Enum
from typing import ClassVar, Literal

from pydantic import BaseModel, Field


class Intent(str, Enum):
    create_request = "create_request"
    transfer = "transfer"
    schedule = "schedule"
    update_contact = "update_contact"
    cancel = "cancel"
    other = "other"


class Action(BaseModel):
    intent: Intent
    amount: int | None = None            # rupees, integer
    date: str | None = None              # ISO 8601, e.g. "2026-11-05"
    account_id: str | None = None        # digits as string, keep leading zeros
    name: str | None = None
    extra: dict = Field(default_factory=dict)

    CRITICAL_FIELDS: ClassVar[tuple[str, ...]] = ("amount", "date", "account_id", "name")

    def critical(self) -> dict:
        return {f: getattr(self, f) for f in self.CRITICAL_FIELDS if getattr(self, f) is not None}


class Sample(BaseModel):
    """One labelled source utterance. Each is recorded once and rendered in 3 conditions."""
    id: str                              # e.g. "s01_u07"
    speaker: str                         # keeps dev/test speaker-disjoint
    split: Literal["dev", "test"]
    audio_file: str                      # filename in data/raw/
    language_code: str                   # Prisma language_code to send, e.g. "te-IN"
    reference_transcript: str
    action: Action                       # final intended action
    superseded: dict = Field(default_factory=dict)  # values the speaker corrected away from
    correction_present: bool = False
    negation_present: bool = False
    risk: Literal["low", "medium", "high", "irreversible"] = "medium"
    tags: list[str] = Field(default_factory=list)   # e.g. ["number", "self_correction", "control"]


class Decision(str, Enum):
    accept = "accept"
    clarify = "clarify"
    escalate = "escalate"


class PolicyOutput(BaseModel):
    decision: Decision
    action: Action | None                # what would execute (if accepted)
    reasons: list[str] = Field(default_factory=list)
    fields_to_confirm: list[str] = Field(default_factory=list)
