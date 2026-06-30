---
name: typecheck
description: Prüft die linmotor-Python-Codebasis mit mypy auf Typfehler und meldet jeden Fund mit Datei, Zeile und konkretem Korrekturvorschlag — ohne Dateien zu verändern. Anwenden, wenn von „Typfehler", „mypy", „type check" oder „vor dem Commit prüfen" die Rede ist oder nachdem ein Feature implementiert wurde.
allowed-tools: Read, Grep, Glob, Bash
---

# Typecheck (linmotor)

Diagnose-Skill: führt die statische Typprüfung aus und berichtet die Befunde. Er
**ändert keine Dateien** — die aktiven Werkzeuge sind auf Lesen und das Ausführen
von `mypy` beschränkt (kein `Edit`/`Write`).

## Ablauf
1. Typprüfung ausführen:
   ```bash
   uv run mypy src
   ```
2. Jeden Fund zusammenfassen: `Datei:Zeile` — Kern des Problems — Korrekturvorschlag
   (als Beschreibung, **nicht** als Edit).
3. Liegen keine Fehler vor: das klar sagen und aufhören.

## Projektwissen (linmotor-spezifisch)
Die mypy-Konfiguration steht in `pyproject.toml` (`disallow_untyped_defs = true`,
`ignore_missing_imports = true`). Daraus folgt:

- **Keine** per-Zeilen-`# type: ignore` für `magpylib`/`matplotlib` ergänzen —
  fehlende Stubs sind bereits global ignoriert. Erscheinen `unused-ignore`-Meldungen,
  ist das vorhandene `# type: ignore` überflüssig und sollte entfernt werden.
- **Rückgabetypen der Analyse-Funktionen** müssen ihren Containertyp tragen, nicht
  `float`:
  - `thrust_curve(...) -> list[float]`
  - `convergence_study(...) -> dict[int, float]`
  - `compare_arrays(...) -> dict[str, float]`
  Ein versehentliches `-> float` ist der häufigste Fund (typischer Modul-2-Schnitzer).
- **numpy-Arrays** als `NDArray[np.float64]` annotieren (siehe `field.py`), nicht als
  blankes `np.ndarray`.
- **Frozen dataclasses** (`MagnetTrack`, `Forcer`, `CoilGeometry`, `Motor`): Felder
  nie per Attributzuweisung ändern, sondern `dataclasses.replace(...)`. mypy meldet
  bei Zuweisung an ein eingefrorenes Feld einen Fehler.
- **`ForceVector`** ist ein `NamedTuple`: `.fx`/`.fz` sind `float`; beim Entpacken die
  Tupel-Form beachten.

## Berichtsformat
```
mypy: N Fund(e)
- src/linmotor/force.py:42  [return-value]  Deklariert -> float, gibt list zurück.
    Vorschlag: Rückgabetyp auf list[float] ändern.
- ...
Empfehlung: <Kurzfazit>
```

## Regeln
- Niemals Dateien ändern; keine `Edit`-/`Write`-Aufrufe.
- `Bash` ausschließlich für `mypy` / `uv run mypy` nutzen.
- Findest du nichts, melde „Typprüfung sauber" und stoppe.
