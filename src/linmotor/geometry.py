"""Geometrie des eisenlosen Linearmotors (2D-Schnitt).

Koordinaten
-----------
* ``x``  : Bewegungsrichtung (entlang der Magnetbahn)
* ``z``  : Luftspaltnormale (Abstand Spule <-> Magnet)
* ``y``  : in die Schnittebene hinein -> Stromrichtung der Leiter

Der Spulenquerschnitt liegt damit in der ``x``-``z``-Ebene; die Modelltiefe
(``conductor_length_m``) misst entlang ``y``.

Einheiten
---------
* Längen / Positionen : Millimeter (mm)   -- konsistent für magpylib
* Modelltiefe / Leiterlänge : Meter (m)   -- für die Kraftberechnung
* Polarisation        : Tesla (T)
* Strom               : Ampere (A)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Modelltiefe-Bezug: alle Magnete sind in y lang genug für den 2D-Schnitt.
MAGNET_LENGTH_Y_MM: float = 100.0


@dataclass(frozen=True)
class MagnetTrack:
    """Magnetbahn: Reihe quaderförmiger Magnete.

    ``halbach=False`` -> alternierende z-Magnetisierung (Standard).
    ``halbach=True``  -> lineares Halbach-Array; die Magnetisierungsrichtung
    rotiert mit der Periode ``2*tau`` und verstärkt das Feld auf einer Seite.
    """

    pole_pitch_mm: float
    n_poles: int
    magnet_width_mm: float
    magnet_height_mm: float
    polarization_T: float = 1.3
    z_mm: float = 0.0
    halbach: bool = False
    n_segments_per_pole: int = 2
    """Nur für Halbach: Segmente pro Polteilung (Diskretisierung der Rotation)."""

    def magnet_top_mm(self) -> float:
        """Oberkante der Magnete (Bezug für den Luftspalt)."""
        return self.z_mm + self.magnet_height_mm / 2.0


def magnet_layout(
    track: MagnetTrack, x_shift_mm: float = 0.0
) -> list[tuple[float, float, float, float, float, float]]:
    """Geometrie + Magnetisierung jedes Magneten.

    Rückgabe: Liste aus ``(x_center, z_center, width, height, p_x, p_z)`` in
    mm bzw. T. ``x_shift_mm`` verschiebt das gesamte (starre) Array entlang x;
    die Magnetisierungsrichtung bleibt an das Array gebunden.
    """
    items: list[tuple[float, float, float, float, float, float]] = []
    if track.halbach:
        n_seg = track.n_segments_per_pole
        seg_w = track.pole_pitch_mm / n_seg
        for k in range(track.n_poles * n_seg + 1):
            x0 = k * seg_w - track.n_poles * n_seg * seg_w / 2.0 #- seg_w / 2.0
            angle = math.pi * x0 / track.pole_pitch_mm + math.pi / 2.0  # Periode 2*tau
            p_x = track.polarization_T * math.cos(angle)
            p_z = track.polarization_T * math.sin(angle)
            items.append(
                (x0 + x_shift_mm, track.z_mm, seg_w, track.magnet_height_mm, p_x, p_z)
            )
    else:
        for i in range(track.n_poles):
            x0 = (i + 0.5) * track.pole_pitch_mm - track.n_poles * track.pole_pitch_mm / 2.0
            sign = -1.0 if i % 2 == 0 else 1.0
            items.append(
                (
                    x0 + x_shift_mm,
                    track.z_mm,
                    track.magnet_width_mm,
                    track.magnet_height_mm,
                    0.0,
                    sign * track.polarization_T,
                )
            )
    return items


@dataclass(frozen=True)
class CoilGeometry:
    """Querschnitt eines Leiterbündels (Spulenschnitt) in der x-z-Ebene.

    Der Querschnitt wird für die Kraftintegration in ``n_cells_x * n_cells_z``
    finite Volumen unterteilt; in jeder Zelle wird B als konstant (Wert im
    Zellmittelpunkt) angenommen.
    """

    width_mm: float
    height_mm: float
    n_cells_x: int = 4
    n_cells_z: int = 4

    def __post_init__(self) -> None:
        if self.width_mm <= 0.0 or self.height_mm <= 0.0:
            raise ValueError("Spulenabmessungen müssen > 0 sein.")
        if self.n_cells_x < 1 or self.n_cells_z < 1:
            raise ValueError("Zellzahlen müssen >= 1 sein.")

    def cell_area_mm2(self) -> int:
        """Fläche einer (gleichförmigen) finiten Volumenzelle in der x-z-Ebene."""
        return (self.width_mm / self.n_cells_x) * (self.height_mm / self.n_cells_z)

    def cell_centers(self) -> list[tuple[float, float]]:
        """Zellmittelpunkte als ``(dx, dz)`` relativ zum Bündelzentrum (mm)."""
        dx = self.width_mm / self.n_cells_x
        dz = self.height_mm / self.n_cells_z
        centers: list[tuple[float, float]] = []
        for i in range(self.n_cells_x):
            cx = -self.width_mm / 2.0 + (i + 0.5) * dx
            for k in range(self.n_cells_z):
                cz = -self.height_mm / 2.0 + (k + 0.5) * dz
                centers.append((cx, cz))
        return centers


@dataclass(frozen=True)
class ConductorBundle:
    """Ein Leiterbündel (eine Spulenseite) im Schnitt."""

    x_center_mm: float
    z_center_mm: float
    polarity: float  # +1.0 (hin) oder -1.0 (rück)
    phase_index: int  # 0=A, 1=B, 2=C


@dataclass(frozen=True)
class Forcer:
    """Eisenloser 3-Phasen-Läufer mit je einer Spule pro Phase."""

    pole_pitch_mm: float
    coil_z_mm: float
    coil: CoilGeometry
    n_turns: int = 50
    peak_current_A: float = 5.0
    conductor_length_m: float = 0.1
    coil_span_mm: float | None = None
    """Abstand Hin-/Rückseite einer Spule; Default = Polteilung tau."""

    def span_mm(self) -> float:
        return self.coil_span_mm if self.coil_span_mm is not None else self.pole_pitch_mm

    def bundles(self) -> list[ConductorBundle]:
        """Alle sechs Leiterbündel (3 Phasen x Hin/Rück), Phasen um 2*tau/3 versetzt."""
        tau = self.pole_pitch_mm
        span = self.span_mm()
        out: list[ConductorBundle] = []
        #coil_gap = 
        for phase in range(3):
            x_phase = phase * (1.0 * tau / 3.0) - span/3.0
            out.append(ConductorBundle(x_phase-span/2, self.coil_z_mm, 1.0, phase))
            out.append(ConductorBundle(x_phase + span/2, self.coil_z_mm, -1.0, phase))
        return out

    def consistency_issues(self) -> list[str]:
        """Geometrische Konsistenz: Spulenbreite gegen beide Überlappungsgrenzen.

        Phasenübergreifend: Bündelabstand = τ/3, daher muss width_mm ≤ τ/3.
        Innerhalb einer Phase: Hin-/Rückseite sind span auseinander, daher width_mm ≤ span.
        """
        issues: list[str] = []
        tau_third = self.pole_pitch_mm / 3.0
        if self.coil.width_mm > tau_third + 1e-9:
            issues.append(
                f"Spulenbreite {self.coil.width_mm:.2f} mm > τ/3 = {tau_third:.2f} mm: "
                "phasenübergreifende Überlappung der Leiterbündel."
            )
        bundles = self.bundles()
        half_w = self.coil.width_mm / 2.0
        for i in range(len(bundles)):
            for j in range(i + 1, len(bundles)):
                a, b = bundles[i], bundles[j]
                if a.phase_index != b.phase_index:
                    continue
                overlap_x = (min(a.x_center_mm, b.x_center_mm) + half_w) - (
                    max(a.x_center_mm, b.x_center_mm) - half_w
                )
                if overlap_x > 1e-9:
                    issues.append(
                        f"Spulenüberlappung in Phase {a.phase_index}: "
                        f"Hin- (x={a.x_center_mm:.2f}) und Rückseite (x={b.x_center_mm:.2f}) "
                        f"überlappen um {overlap_x:.2f} mm."
                    )
        return issues


@dataclass(frozen=True)
class Motor:
    """Vollständiger Motor = Magnetbahn + Läufer."""

    track: MagnetTrack
    forcer: Forcer

    def consistency_issues(self) -> list[str]:
        """Sammelt alle Konsistenzprobleme (Spulenüberlappung + Luftspalt)."""
        issues = list(self.forcer.consistency_issues())
        coil_bottom = self.forcer.coil_z_mm - self.forcer.coil.height_mm / 2.0
        if coil_bottom <= self.track.magnet_top_mm() + 1e-9:
            issues.append(
                f"Spule kollidiert mit Magneten: Unterkante {coil_bottom:.2f} mm "
                f"<= Magnetoberkante {self.track.magnet_top_mm():.2f} mm."
            )
        return issues
