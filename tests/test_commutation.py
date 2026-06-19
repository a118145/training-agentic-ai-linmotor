"""Tests der Kommutierung -- laufen ohne magpylib (reine Mathematik)."""

from __future__ import annotations

import math

from linmotor.commutation import electrical_angle, phase_currents


def test_constant_power() -> None:
    """Summe der Stromquadrate ist lageunabhängig konstant (3/2 * I_peak^2)."""
    peak = 5.0
    for x_mm in range(0, 48):
        theta_e = electrical_angle(float(x_mm), pole_pitch_mm=12.0)
        i_a, i_b, i_c = phase_currents(theta_e, peak)
        power = i_a**2 + i_b**2 + i_c**2
        assert math.isclose(power, 1.5 * peak**2, abs_tol=1e-9)


def test_electrical_period() -> None:
    """Eine elektrische Periode entspricht zwei Polteilungen."""
    tau = 12.0
    assert math.isclose(electrical_angle(2 * tau, tau), 2 * math.pi, abs_tol=1e-9)
