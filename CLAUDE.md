# linmotor

2D-Auslegung **eisenloser Linearmotoren**. Magnetfelder über `magpylib`,
Schub über die Lorentzkraft.

## Setup
```bash
uv sync --extra dev
uv run pytest
```

## Konventionen
- Paketmanager ist **uv**.
- Längen in **mm** (für magpylib), Leiterlänge in **m**, B in **T**, Kraft in **N**.
- Datenmodell nutzt **frozen dataclasses** (`geometry.py`).

> Hinweis: Diese Datei wird in Modul 1 der Schulung bewusst erweitert.
