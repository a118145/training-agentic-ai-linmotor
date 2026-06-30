"""Visualisierung des Motorschnitts mit PNG-Export.

Zeichnet den x-z-Schnitt: Magnete (mit Magnetisierungspfeilen), die
Spulenbündel (mit Stromrichtung) und optional das B-Feld sowie den
resultierenden Kraftvektor. Backend ``Agg`` -> kein Display-Server nötig
(headless / Docker tauglich).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless: direkt nach PNG rendern
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from .commutation import electrical_angle, phase_currents  # noqa: E402
from .geometry import Motor, magnet_layout  # noqa: E402


def plot_motor(
    motor: Motor,
    path: str,
    displacement_mm: float = 0.0,
    theta_offset: float = 0.0,
    with_field: bool = True,
    dpi: int = 150,
) -> str:
    """Rendert den Motorschnitt und speichert ihn als PNG. Gibt den Pfad zurück.

    Feld- und Kraft-Overlay benötigen magpylib; fehlt es, wird nur die Geometrie
    gezeichnet (mit Hinweis).
    """
    track = motor.track
    forcer = motor.forcer
    coil = forcer.coil

    fig, ax = plt.subplots(figsize=(11, 5))

    # --- Magnete -------------------------------------------------------------
    for x_c, z_c, width, height, p_x, p_z in magnet_layout(track, 0):
        norm = np.hypot(p_x, p_z) or 1.0
        # Farbe nach z-Komponente der Magnetisierung (rot = +z, blau = -z)
        shade = 0.5 + 0.5 * (p_z / norm)
        ax.add_patch(
            Rectangle(
                (x_c - width / 2, z_c - height / 2),
                width,
                height,
                facecolor=(shade, 0.25, 1.0 - shade),
                edgecolor="black",
                linewidth=0.5,
                alpha=0.85,
            )
        )
        ax.arrow(
            x_c, z_c,
            0.30 * width * p_x / norm, 0.30 * height * p_z / norm,
            head_width=0.6, head_length=0.6, fc="white", ec="white", length_includes_head=True,
        )

    # --- B-Feld (optional, benötigt magpylib) --------------------------------
    field_ok = False
    if with_field:
        try:
            from .field import bfield, build_track

            x_min = forcer.bundles()[0].x_center_mm - 2*coil.width_mm + theta_offset/np.pi * forcer.pole_pitch_mm + displacement_mm
            x_max = forcer.bundles()[-1].x_center_mm + 2*coil.width_mm + theta_offset/np.pi * forcer.pole_pitch_mm + displacement_mm
            z_lo = track.magnet_top_mm() + 0.2
            z_hi = forcer.coil_z_mm + 1.5*coil.height_mm
            gx, gz = np.meshgrid(
                np.linspace(x_min, x_max, 45), np.linspace(z_lo, z_hi, 16)
            )
            pts = np.column_stack([gx.ravel(), np.zeros(gx.size), gz.ravel()])
            b = bfield(build_track(track, displacement_mm), pts)
            bx = b[:, 0].reshape(gx.shape)
            bz = b[:, 2].reshape(gx.shape)
            ax.streamplot(gx, gz, bx, bz, density=1.1, color="0.35", linewidth=0.6, arrowsize=0.7)
            field_ok = True
        except Exception:  # magpylib fehlt o. ä. -> Geometrie genügt
            field_ok = False

    # --- Spulenbündel mit Stromrichtung --------------------------------------
    theta_e = electrical_angle(displacement_mm, track.pole_pitch_mm) + theta_offset
    currents = phase_currents(theta_e, forcer.peak_current_A)
    phase_color = {0: "#d62728", 1: "#2ca02c", 2: "#1f77b4"}
    for bundle in forcer.bundles():
        ax.add_patch(
            Rectangle(
                (bundle.x_center_mm - coil.width_mm / 2 + theta_offset/np.pi * forcer.pole_pitch_mm + displacement_mm, bundle.z_center_mm - coil.height_mm / 2),
                coil.width_mm,
                coil.height_mm,
                facecolor=phase_color[bundle.phase_index],
                edgecolor="black",
                linewidth=0.6,
                alpha=0.7,
            )
        )
        i_signed = bundle.polarity * currents[bundle.phase_index]
        symbol = "$\\odot$" if i_signed <= 0 else "$\\otimes$"  # Strom aus/in Ebene
        ax.text(
            bundle.x_center_mm+ theta_offset/np.pi * forcer.pole_pitch_mm + displacement_mm, bundle.z_center_mm, symbol,
            ha="center", va="center", fontsize=11, color="white",
        )

    # --- resultierender Kraftvektor (optional, benötigt magpylib) ------------
    title = f"Linearmotor-Schnitt (Verschiebung {displacement_mm:.1f} mm)"
    if with_field and field_ok:
        try:
            from .force import force

            fvec = force(motor, displacement_mm, theta_offset)
            cx = float(np.mean([b.x_center_mm for b in forcer.bundles()])) + theta_offset/np.pi * forcer.pole_pitch_mm+displacement_mm
            cz = forcer.coil_z_mm
            scale = track.pole_pitch_mm / (fvec.magnitude or 1.0)
            ax.arrow(
                cx, cz, scale * fvec.fx, scale * fvec.fz,
                head_width=1.0, head_length=1.2, fc="black", ec="black",
                length_includes_head=True, zorder=5,
            )
            title += (
                f"  |  F=({fvec.fx:.1f}, {fvec.fz:.1f}) N, |F|={fvec.magnitude:.1f} N"
            )
        except Exception:
            pass
    elif with_field and not field_ok:
        title += "  |  (Feld/Kraft-Overlay benötigt magpylib)"

    ax.set_xlabel("x  /  mm  (Bewegungsrichtung)")
    ax.set_ylabel("z  /  mm  (Luftspalt)")
    ax.set_title(title)
    bundles = forcer.bundles()
    track_min_max = (track.n_poles * track.pole_pitch_mm + track.magnet_width_mm ) / 2.0 + 2.0
    x_lo = min(b.x_center_mm for b in bundles) - coil.width_mm - 2.0
    x_hi = max(b.x_center_mm for b in bundles) + coil.width_mm + 2.0
    ax.set_xlim(min(x_lo, -track_min_max), max(x_hi, track_min_max))
    ax.set_ylim(
        track.z_mm - track.magnet_height_mm,
        forcer.coil_z_mm + coil.height_mm + 1.0,
    )
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def plot_thrust_curve(
    motor: Motor,
    path: str,
    theta_offset: float = 0.0,
    n_points: int = 120,
    dpi: int = 150,
) -> str:
    """Schub über eine elektrische Periode als PNG (benötigt magpylib)."""
    from .force import thrust_curve

    xs = list(np.linspace(-motor.track.pole_pitch_mm, motor.track.pole_pitch_mm, n_points))
    fx = thrust_curve(motor, xs, theta_offset)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(xs, fx, color="#1f77b4")
    ax.axhline(sum(fx) / len(fx), color="0.5", linestyle="--", linewidth=0.8, label="Mittelwert")
    ax.set_xlabel("Array-Verschiebung  /  mm")
    ax.set_ylabel("Schub $F_x$  /  N")
    ax.set_title("Schubverlauf über eine elektrische Periode")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def plot_thrust_comparison(
    motor_std: Motor,
    motor_hal: Motor,
    path: str,
    n_points: int = 120,
    dpi: int = 150,
) -> str:
    """Vergleich der Schubkurven (Standard vs. Halbach) als PNG (benötigt magpylib)."""
    from .force import find_commutation_offset, thrust_curve

    offset_std = find_commutation_offset(motor_std)
    offset_hal = find_commutation_offset(motor_hal)

    tau = motor_std.track.pole_pitch_mm
    xs = list(np.linspace(0.0, 2.0 * tau, n_points, endpoint=False))

    fx_std = thrust_curve(motor_std, xs, offset_std)
    fx_hal = thrust_curve(motor_hal, xs, offset_hal)

    mean_std = sum(fx_std) / len(fx_std)
    mean_hal = sum(fx_hal) / len(fx_hal)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(xs, fx_std, color="#1f77b4", label="Standard")
    ax.plot(xs, fx_hal, color="#ff7f0e", label="Halbach")
    ax.axhline(mean_std, color="#1f77b4", linestyle="--", linewidth=0.8,
               label=f"Mittelwert Standard ({mean_std:.2f} N)")
    ax.axhline(mean_hal, color="#ff7f0e", linestyle="--", linewidth=0.8,
               label=f"Mittelwert Halbach ({mean_hal:.2f} N)")
    ax.set_xlabel("Array-Verschiebung  /  mm")
    ax.set_ylabel("Schub $F_x$  /  N")
    ax.set_title("Schubvergleich: Standard vs. Halbach")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path
