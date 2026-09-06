"""Tests: risk engine classification + ordering."""
from __future__ import annotations

import pytest

from app.services import risk_engine as re


@pytest.mark.parametrize("prob,expected", [
    (0, "LOW"),
    (19.9, "LOW"),
    (20, "MODERATE"),
    (39.9, "MODERATE"),
    (40, "HIGH"),
    (59.9, "HIGH"),
    (60, "VERY HIGH"),
    (79.9, "VERY HIGH"),
    (80, "CRITICAL"),
    (100, "CRITICAL"),
])
def test_classify_boundaries(prob, expected):
    assert re.classify(prob) == expected


def test_classify_clamps():
    assert re.classify(-50) == "LOW"
    assert re.classify(999) == "CRITICAL"


def test_risk_order_complete():
    assert re.RISK_ORDER == ["LOW", "MODERATE", "HIGH", "VERY HIGH", "CRITICAL"]


def test_risk_color_present():
    for r in re.RISK_ORDER:
        assert re.risk_color(r).startswith("#")


def test_risk_level_increasing():
    levels = [re.risk_level(r) for r in re.RISK_ORDER]
    assert levels == sorted(levels)
    assert re.risk_level("CRITICAL") == 4
