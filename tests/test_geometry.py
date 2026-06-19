"""Geometrie-Tests -- laufen ohne magpylib (reine Python-Logik)."""

from __future__ import annotations

import math

import pytest

from linmotor.geometry import CoilGeometry, Forcer, MagnetTrack, Motor, magnet_layout


def test_cell_discretisation() -> None:
    coil = CoilGeometry(width_mm=3.0, height_mm=4.0, n_cells_x=4, n_cells_z=5)
    centers = coil.cell_centers()
    assert len(centers) == 4 * 5
    # Summe der Zellflächen == Querschnittsfläche
    assert math.isclose(coil.cell_area_mm2() * len(centers), 3.0 * 4.0, abs_tol=1e-9)
    # Mittelpunkte liegen innerhalb des Querschnitts
    assert all(abs(dx) <= 1.5 and abs(dz) <= 2.0 for dx, dz in centers)


def test_invalid_coil_raises() -> None:
    with pytest.raises(ValueError):
        CoilGeometry(width_mm=0.0, height_mm=4.0)


def _forcer(width: float) -> Forcer:
    return Forcer(
        pole_pitch_mm=12.0,
        coil_z_mm=5.5,
        coil=CoilGeometry(width_mm=width, height_mm=4.0),
    )


def test_overlap_check() -> None:
    # schmale Spulen (3 mm) passen in die 4-mm-Lücken -> keine Überlappung
    assert _forcer(3.0).consistency_issues() == []
    # breite Spulen (6 mm) überlappen
    assert _forcer(6.0).consistency_issues() != []


def test_air_gap_check() -> None:
    track = MagnetTrack(pole_pitch_mm=12.0, n_poles=6, magnet_width_mm=10.0, magnet_height_mm=5.0)
    bad = Motor(track=track, forcer=_forcer(3.0).__class__(
        pole_pitch_mm=12.0, coil_z_mm=2.0, coil=CoilGeometry(3.0, 4.0)))
    assert any("Magneten" in m for m in bad.consistency_issues())


def test_halbach_layout_rotates() -> None:
    track = MagnetTrack(12.0, 4, 10.0, 5.0, halbach=True, n_segments_per_pole=4)
    layout = magnet_layout(track)
    assert len(layout) == 4 * 4
    # erstes Segment ~ +z, viertel Periode später ~ +x
    _, _, _, _, px0, pz0 = layout[0]
    assert pz0 > 0.9 * track.polarization_T
    _, _, _, _, px1, _ = layout[1]
    assert px1 > 0.5  # x-Komponente steigt
