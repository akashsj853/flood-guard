"""
FloodGuard AI — impact / population exposure service.

Estimates the population potentially exposed to flooding. This is an ESTIMATE
(population x flood probability) and must always be labelled as such in the UI.
It is NOT a count of people who will definitely be affected.
"""
from __future__ import annotations


def estimate_population_exposure(population: float, probability: float) -> float:
    """ESTIMATE = population x flood_probability (probability in 0..100)."""
    return round(population * max(0.0, min(100.0, float(probability))) / 100.0, 0)


def exposure_band(exposure: float) -> str:
    if exposure >= 5000:
        return "SEVERE"
    if exposure >= 1500:
        return "SIGNIFICANT"
    if exposure >= 200:
        return "MODERATE"
    return "LOW"
