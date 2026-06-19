# linmotor

Kompakte Codebasis zur **2D-Auslegung eisenloser Linearmotoren**.

## Physik
- **Magnetbahn** (`MagnetTrack`): Permanentmagnete, alternierend **oder Halbach**
  (`halbach=True`). Feld über `magpylib`.
- **Läufer** (`Forcer`): eisenlos, 3 Phasen, je eine Spule. Jeder Spulenschnitt
  (`CoilGeometry`) wird in **finite Volumen** zerlegt; in jeder Zelle gilt B als
  konstant (Mittelpunktswert).
- **Kraft**: echtes Volumenintegral der Lorentzkraft `F = Σ (J × B) · dV`. Das
  Ergebnis ist ein **Vektor in der x-z-Ebene** (`ForceVector(fx, fz)`) — Schub
  *und* Normalkraft, je nach Magnetanordnung.
- **Kinematik**: Spule fest, **Magnet-Array wird verschoben** und gleichzeitig
  kommutiert. Der Kommutierungsoffset wird einmalig per **Phasenfindung**
  bestimmt (`find_commutation_offset`).

## Schnellstart
```bash
uv sync --extra dev
uv run pytest
uv run python - <<'PY'
import linmotor as lm
m = lm.example_motor(halbach=True)
print("Konsistenz:", m.consistency_issues() or "OK")
offset = lm.find_commutation_offset(m)          # einmalig nach Aufbau
f = lm.force(m, displacement_mm=2.0, theta_offset=offset)
print(f"F = ({f.fx:.2f}, {f.fz:.2f}) N, |F| = {f.magnitude:.2f} N")
lm.__dict__  # API
from linmotor.visualize import plot_motor
plot_motor(m, "motor.png", displacement_mm=2.0, theta_offset=offset)  # PNG-Export
PY
```

## Struktur
```
src/linmotor/
  geometry.py     # MagnetTrack, CoilGeometry, ConductorBundle, Forcer, Motor,
                  #   magnet_layout(); Konsistenzchecks (Überlappung, Luftspalt)
  field.py        # magpylib-Wrapper: build_track(track, x_shift), bfield()
  commutation.py  # Phasenströme aus der Position
  force.py        # ForceVector, force(), thrust(), find_commutation_offset(),
                  #   thrust_curve(), ripple()
  visualize.py    # plot_motor()/plot_thrust_curve() -> PNG (Agg, headless)
tests/
  test_geometry.py     # ohne magpylib lauffähig
  test_commutation.py  # ohne magpylib lauffähig
  test_visualize.py    # PNG-Export (Geometrie) ohne magpylib lauffähig
  test_force.py        # benötigt magpylib
docs/
  SCHULUNG.md     # Trainer-Leitfaden (5 Module)
```

> Hinweis: zielt auf magpylib ≥ 5 (`polarization` in Tesla, `getB` liefert Tesla).
