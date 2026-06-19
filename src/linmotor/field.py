"""Magnetfeld-Berechnung über magpylib.

Baut die Magnetbahn (Standard oder Halbach) aus der gemeinsamen
Layout-Beschreibung in :func:`linmotor.geometry.magnet_layout` und wertet die
Flussdichte an beliebigen Punkten aus.
"""

from __future__ import annotations

import magpylib as magpy
import numpy as np
from numpy.typing import NDArray

from .geometry import MAGNET_LENGTH_Y_MM, MagnetTrack, magnet_layout


def build_track(track: MagnetTrack, x_shift_mm: float = 0.0) -> magpy.Collection:
    """Magnetbahn als magpylib-Collection; ``x_shift_mm`` verschiebt das Array."""
    collection = magpy.Collection()
    for x_c, z_c, width, height, p_x, p_z in magnet_layout(track, x_shift_mm):
        collection.add(
            magpy.magnet.Cuboid(
                polarization=(p_x, 0.0, p_z),
                dimension=(width, MAGNET_LENGTH_Y_MM, height),
                position=(x_c, 0.0, z_c),
            )
        )
    return collection


def bfield(
    collection: magpy.Collection, points_mm: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Flussdichte B (Tesla) an ``points_mm`` (Form ``(N, 3)`` in mm)."""
    return np.asarray(collection.getB(points_mm), dtype=np.float64)
