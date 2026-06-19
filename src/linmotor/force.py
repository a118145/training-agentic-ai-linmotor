"""Kraftberechnung über das Volumenintegral der Lorentzkraft.

Jeder Spulenquerschnitt wird in finite Volumen unterteilt. In jeder Zelle gilt B
als konstant (Mittelpunktswert). Mit Stromdichte ``J = J_y * y_hat`` ist die
Kraftdichte ``f = J x B`` und damit

    f_x = J_y * B_z          f_z = -J_y * B_x

Die Gesamtkraft ist das Integral ``F = sum( f * dV )`` mit
``dV = Zellfläche(x,z) * Modelltiefe(y)``. Die resultierende Kraft liegt
allgemein in der x-z-Ebene -- je nach Magnetanordnung (z. B. Halbach) hat sie
neben dem Schub (x) auch eine Normalkomponente (z).

Konvention der Kinematik: die Spule steht fest, das Magnet-Array wird um
``displacement_mm`` verschoben; gleichzeitig wird kommutiert.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np

from .commutation import electrical_angle, phase_currents
from .field import bfield, build_track
from .geometry import Motor


class ForceVector(NamedTuple):
    """Kraft in der x-z-Ebene (in Newton)."""

    fx: float  # Schub (Bewegungsrichtung)
    fz: float  # Normalkraft (Luftspaltrichtung)

    @property
    def magnitude(self) -> float:
        return float(np.hypot(self.fx, self.fz))


def force(motor: Motor, displacement_mm: float = 0.0, theta_offset: float = 0.0) -> ForceVector:
    """Kraftvektor (F_x, F_z) bei Array-Verschiebung ``displacement_mm``.

    ``theta_offset`` ist der Kommutierungs-Phasenoffset aus
    :func:`find_commutation_offset`.
    """
    track = motor.track
    forcer = motor.forcer
    coil = forcer.coil

    collection = build_track(track, x_shift_mm=-displacement_mm)
    # Bei +displacement bewegt sich das Feldmuster in Richtung -x; die Kommutierung läuft
    # synchron mit der relativen Lage (Spule relativ zum Array = +displacement).
    theta_e = electrical_angle(displacement_mm, track.pole_pitch_mm) + theta_offset
    #print("theta_e:", theta_e)
    currents = phase_currents(theta_e, forcer.peak_current_A)

    a_cross_m2 = coil.width_mm * coil.height_mm * 1e-6
    dvol_m3 = (coil.cell_area_mm2() * 1e-6) * forcer.conductor_length_m
    cells = coil.cell_centers()

    points: list[tuple[float, float, float]] = []
    current_density: list[float] = []
    for bundle in forcer.bundles():
        i_phase = currents[bundle.phase_index]
        # gleichförmige Stromdichte J_y über den Querschnitt (A/m^2)
        j_y = bundle.polarity * forcer.n_turns * i_phase / a_cross_m2
        for dx, dz in cells:
            points.append((bundle.x_center_mm + dx, 0.0, bundle.z_center_mm + dz))
            current_density.append(j_y)

    b = bfield(collection, np.asarray(points, dtype=np.float64))  # (M, 3) in T
    j = np.asarray(current_density, dtype=np.float64)

    fx = float(np.sum(j * b[:, 2]) * dvol_m3)   # f_x = J_y * B_z
    fz = float(-np.sum(j * b[:, 0]) * dvol_m3)  # f_z = -J_y * B_x
    return ForceVector(fx, fz)


def thrust(motor: Motor, displacement_mm: float = 0.0, theta_offset: float = 0.0) -> float:
    """Bequemlichkeits-Wrapper: nur die Schubkomponente F_x (N)."""
    return force(motor, displacement_mm, theta_offset).fx


def find_commutation_offset(motor: Motor, n_angles: int = 360) -> float:
    """Phasenfindung: Kommutierungsoffset, der bei Verschiebung 0 den Schub maximiert.

    Einmalig nach dem Aufbau des Motors aufzurufen. Für ein Halbach-Array ist die
    räumliche Feldphase verschoben, sodass der Offset nicht trivial bei 0 liegt.
    Anschließend wird mit diesem Offset bei beliebiger Verschiebung kommutiert.
    """
    angles = np.linspace(0.0, 2.0 * np.pi, n_angles, endpoint=False)
    best_angle = 0.0
    best_fx = -np.inf
    for angle in angles:
        fx = force(motor, displacement_mm=0.0, theta_offset=float(angle)).fx
        if fx > best_fx:
            best_fx = fx
            best_angle = float(angle)
    return best_angle


def thrust_curve(
    motor: Motor, displacements_mm: list[float], theta_offset: float = 0.0
) -> list[float]:
    """Schub F_x an mehreren Verschiebungen (für Rippel-/KPI-Analysen)."""
    return [thrust(motor, d, theta_offset) for d in displacements_mm]


def ripple(samples: list[float]) -> float:
    """Relatives Schubrippel ``(max - min) / mean``."""
    mean = sum(samples) / len(samples)
    print(f"Mean: {mean}, max: {max(samples)}, min: {min(samples)}")
    return (max(samples) - min(samples)) / mean
