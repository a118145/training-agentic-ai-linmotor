"""Visualisierungs-Test: PNG-Export (Geometrie funktioniert ohne magpylib)."""

from __future__ import annotations

from pathlib import Path

from linmotor import example_motor
from linmotor.visualize import plot_motor


def test_png_export(tmp_path: Path) -> None:
    out = tmp_path / "motor.png"
    # with_field=False -> kein magpylib nötig
    plot_motor(example_motor(), str(out), with_field=False)
    assert out.exists() and out.stat().st_size > 1000
