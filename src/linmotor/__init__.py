"""linmotor -- 2D-Auslegung eisenloser Linearmotoren (magpylib-basiert)."""

from __future__ import annotations

from .commutation import electrical_angle, phase_currents
from .field import bfield, build_track
from .force import (
    ForceVector,
    find_commutation_offset,
    force,
    ripple,
    thrust,
    thrust_curve,
)
from .geometry import (
    CoilGeometry,
    ConductorBundle,
    Forcer,
    MagnetTrack,
    Motor,
    magnet_layout,
)

__all__ = [
    "MagnetTrack",
    "CoilGeometry",
    "ConductorBundle",
    "Forcer",
    "Motor",
    "magnet_layout",
    "build_track",
    "bfield",
    "electrical_angle",
    "phase_currents",
    "ForceVector",
    "force",
    "thrust",
    "thrust_curve",
    "ripple",
    "find_commutation_offset",
    "example_motor",
    "example_motor_training",
]

__version__ = "0.2.0"


def example_motor(halbach: bool = False) -> Motor:
    """Kompaktes, konsistentes Beispiel (Spulen überlappen nicht)."""
    track = MagnetTrack(
        pole_pitch_mm=12.0,
        n_poles=8,
        magnet_width_mm=10.0,
        magnet_height_mm=5.0,
        polarization_T=1.3,
        halbach=halbach,
    )
    forcer = Forcer(
        pole_pitch_mm=12.0,
        coil_z_mm=track.magnet_top_mm() + 1.0 + 2.0,  # Luftspalt 1.0 mm + halbe Spulenhöhe
        coil=CoilGeometry(width_mm=3.8, height_mm=4.0, n_cells_x=4, n_cells_z=4),
        n_turns=50,
        peak_current_A=5.0,
        conductor_length_m=0.1,
    )
    return Motor(track=track, forcer=forcer)


def example_motor_training(halbach: bool = False) -> Motor:
    """Kompaktes, konsistentes Beispiel (Spulen überlappen nicht)."""
    track = MagnetTrack(
        pole_pitch_mm=12.0,
        n_poles=2,
        magnet_width_mm=10.0,
        magnet_height_mm=5.0,
        polarization_T=1.3,
        halbach=halbach,
    )
    forcer = Forcer(
        pole_pitch_mm=12.0,
        coil_z_mm=track.magnet_top_mm() + 1.0 + 2.0,  # Luftspalt 1.0 mm + halbe Spulenhöhe
        coil=CoilGeometry(width_mm=3.8, height_mm=4.0, n_cells_x=4, n_cells_z=4),
        n_turns=50,
        peak_current_A=5.0,
        conductor_length_m=0.1,
    )
    return Motor(track=track, forcer=forcer)
