"""Kraft-Tests -- benötigen magpylib (werden sonst übersprungen)."""

from __future__ import annotations

import pytest

pytest.importorskip("magpylib")

from linmotor import (  # noqa: E402
    example_motor,
    find_commutation_offset,
    force,
    peak_thrust,
    ripple,
    thrust_curve,
)


def test_force_vector_after_phase_finding() -> None:
    motor = example_motor()
    offset = find_commutation_offset(motor)
    fvec = force(motor, displacement_mm=0.0, theta_offset=offset)
    assert fvec.fx > 0.0  # Schub positiv nach Phasenfindung


def test_low_ripple_when_commutated() -> None:
    """Bei gefundenem Offset bleibt der Schub über die Verschiebung ~konstant."""
    motor = example_motor()
    offset = find_commutation_offset(motor)
    xs = [0.5 * k for k in range(int(2 * motor.track.pole_pitch_mm / 0.5))]
    samples = thrust_curve(motor, xs, theta_offset=offset)
    assert min(samples) > 0.0
    assert ripple(samples) < 0.6  # lockere Schranke; engeres Rippel via Halbach/verteilte Wicklung


def test_peak_thrust_bounds() -> None:
    """peak_thrust gibt (min, max) zurück; min <= max, beide positiv nach Phasenfindung."""
    motor = example_motor()
    offset = find_commutation_offset(motor)
    lo, hi = peak_thrust(motor, theta_offset=offset)
    assert lo <= hi
    assert lo > 0.0, "minimaler Schub sollte nach Phasenfindung positiv sein"


def test_peak_thrust_consistent_with_thrust_curve() -> None:
    """peak_thrust liefert dasselbe Ergebnis wie min/max der manuell berechneten Kurve."""
    import numpy as np

    motor = example_motor()
    offset = find_commutation_offset(motor)
    tau = motor.track.pole_pitch_mm
    xs = list(np.linspace(0.0, 2.0 * tau, 120, endpoint=False))
    samples = thrust_curve(motor, xs, theta_offset=offset)
    lo, hi = peak_thrust(motor, theta_offset=offset, n_points=120)
    assert lo == min(samples)
    assert hi == max(samples)


def test_halbach_offset_differs() -> None:
    """Phasenfindung liefert für Halbach einen anderen Offset als für Standard."""
    std_offset = find_commutation_offset(example_motor(halbach=False))
    hal_offset = find_commutation_offset(example_motor(halbach=True))
    assert abs(std_offset - hal_offset) > 1e-3
