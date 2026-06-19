"""Kommutierung: Phasenströme als Funktion der Läuferposition.

Sinusförmige Kommutierung. Der elektrische Winkel ist an die Position
gekoppelt; die elektrische Periode entspricht zwei Polteilungen (2*tau).
Bei feldorientierter Bestromung ist die Summe der Quadrate der drei
Phasenströme konstant (3/2 * I_peak^2) -> theoretisch rippelfreier Schub.
"""

from __future__ import annotations

import math

_PHASE_OFFSET = 1.0 * math.pi / 3.0  # 60° elektrisch


def electrical_angle(x_forcer_mm: float, pole_pitch_mm: float) -> float:
    """Elektrischer Winkel theta_e aus der mechanischen Läuferposition."""
    return math.pi * x_forcer_mm / pole_pitch_mm


def phase_currents(theta_e: float, peak_current_A: float) -> tuple[float, float, float]:
    """Phasenströme (I_A, I_B, I_C) bei feldorientierter Kommutierung."""
    print(
        peak_current_A * math.sin(theta_e - 1 * _PHASE_OFFSET),
        peak_current_A * math.sin(theta_e),
        peak_current_A * math.sin(theta_e + 1 * _PHASE_OFFSET),
    )
    return (
        peak_current_A * math.sin(theta_e - 1 * _PHASE_OFFSET),
        peak_current_A * math.sin(theta_e),
        peak_current_A * math.sin(theta_e + 1 * _PHASE_OFFSET),
    )
