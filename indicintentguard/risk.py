"""Calibrated risk model + cost-sensitive decision rule.

P(wrong action | evidence) = sigmoid(b + w . f)
Clarify when P * C_error(risk tier) > C_clarify. Irreversible actions always confirm;
context violations escalate.

Default weights are priors set by hand before seeing benchmark results; `fit` refines
them on the dev split with L2 regularisation *toward the prior*, so a small dev set
cannot swing them wildly. Never fit on the test split.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .evidence import FEATURES

PRIOR_BIAS = -4.5
PRIOR_W = {
    "correction_resolved": 1.5, "multiple_unresolved": 3.5, "negated_only": 3.5,
    "itn_literal_mismatch": 3.0, "confusable_amount": 0.8, "confusable_x_degraded": 1.2,
    "truncated": 1.0, "low_word_rate": 1.0, "narrowband": 0.5, "low_snr": 0.8,
    "missing_field": 6.0, "context_violation": 6.0,
}
# Cost of executing a wrong action, in units of "one clarification turn".
DEFAULT_ERROR_COST = {"low": 2.0, "medium": 10.0, "high": 40.0}
INTENT_RISK = {"transfer": "high", "cancel": "high", "update_contact": "high",
               "create_request": "medium", "schedule": "low", "other": "medium"}


@dataclass
class RiskModel:
    bias: float = PRIOR_BIAS
    w: dict = field(default_factory=lambda: dict(PRIOR_W))
    error_cost: dict = field(default_factory=lambda: dict(DEFAULT_ERROR_COST))
    clarify_cost: float = 1.0

    def prob(self, f: dict) -> float:
        z = self.bias + sum(self.w.get(k, 0.0) * f.get(k, 0.0) for k in FEATURES)
        return float(1 / (1 + np.exp(-z)))

    def threshold(self, tier: str) -> float:
        return self.clarify_cost / self.error_cost[tier]

    def fit(self, X: list[dict], y: list[int], l2: float = 1.0, lr: float = 0.1, steps: int = 2000) -> "RiskModel":
        A = np.array([[x[k] for k in FEATURES] for x in X], dtype=float)
        t = np.array(y, dtype=float)
        w0 = np.array([PRIOR_W[k] for k in FEATURES])
        w, b = w0.copy(), PRIOR_BIAS
        for _ in range(steps):
            p = 1 / (1 + np.exp(-(A @ w + b)))
            g = p - t
            w -= lr * (A.T @ g / len(t) + l2 * (w - w0) / len(t))
            b -= lr * (g.mean() + l2 * (b - PRIOR_BIAS) / len(t))
        self.w = dict(zip(FEATURES, map(float, w)))
        self.bias = float(b)
        return self

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps({"bias": self.bias, "w": self.w, "error_cost": self.error_cost,
                                          "clarify_cost": self.clarify_cost}, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "RiskModel":
        d = json.loads(Path(path).read_text())
        return cls(bias=d["bias"], w=d["w"], error_cost=d["error_cost"], clarify_cost=d["clarify_cost"])
