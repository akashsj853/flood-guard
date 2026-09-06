"""
FloodGuard AI — risk engine.

Maps a flood probability (0..100) to an operational risk category.

Thresholds (operational priority, kept separate from the raw model probability):
  0-20   LOW
  20-40  MODERATE
  40-60  HIGH
  60-80  VERY HIGH
  80-100 CRITICAL
"""
from __future__ import annotations


# Ordered low -> high for lookup.
_THRESHOLDS = [
    (0, 20, "LOW", "#22c55e"),
    (20, 40, "MODERATE", "#eab308"),
    (40, 60, "HIGH", "#f97316"),
    (60, 80, "VERY HIGH", "#ef4444"),
    (80, 100.0001, "CRITICAL", "#b91c1c"),
]

RISK_COLORS = {name: color for _, _, name, color in _THRESHOLDS}
RISK_ORDER = ["LOW", "MODERATE", "HIGH", "VERY HIGH", "CRITICAL"]


def classify(probability: float) -> str:
    """Return the risk category for a probability in [0, 100]."""
    p = max(0.0, min(100.0, float(probability)))
    for lo, hi, name, _ in _THRESHOLDS:
        if lo <= p < hi:
            return name
    return "CRITICAL"


def risk_color(risk: str) -> str:
    return RISK_COLORS.get(risk, "#6b7280")


def risk_level(risk: str) -> int:
    """Severity index 0..4 (useful for sorting/comparison)."""
    return RISK_ORDER.index(risk) if risk in RISK_ORDER else 0
