# Claude-Code-Schulung: Linearmotor-Auslegung als roter Faden

**Zielgruppe:** Ingenieur:innen mit Python-Grundlagen, die Claude Code produktiv
einsetzen wollen.
**Durchgehendes Beispiel:** `linmotor` — eine kompakte Codebasis zur 2D-Auslegung
**eisenloser** Linearmotoren (Feld via `magpylib`, Kraft via Lorentz-Volumenintegral).

Die Codebasis (Baseline **v0.2**) ist klein genug, um sie auf einen Blick zu
überschauen, und wird über die fünf Module **schrittweise erweitert**. Am Ende ist
sie selbst das **Backend eines MCP-Servers**, den man in Claude einbinden kann.

---

## Was v0.2 bereits mitbringt

Damit niemand „ins Leere" plant: Die Baseline enthält schon

- Magnetbahn **Standard und Halbach** (`MagnetTrack(halbach=...)`),
- den **vollen Kraftvektor** `ForceVector(fx, fz)` über ein **Finite-Volumen-Integral**
  des Spulenquerschnitts (`CoilGeometry`),
- **Phasenfindung** (`find_commutation_offset`) + Kommutierung bei verschobenem Array,
- **Konsistenzchecks** (Spulenüberlappung, Luftspalt),
- **PNG-Visualisierung** (`visualize.plot_motor`).

Die Module bauen darauf auf — sie analysieren, erweitern und verpacken diese Basis.

---

## Der rote Faden

| Session | Modul | Thema | Ergebnis auf der Codebasis |
|--------:|------:|-------|----------------------------|
| 1 | 0 | Setup & Überblick | v0.2 läuft, Tests grün, erstes PNG |
| 1 | 1 | Arbeiten in der Codebasis | `CLAUDE.md` angereichert, kleine Verbesserung + Test |
| 1 | 2 | Plan Mode (**Feature-Baukasten**) | eine der Optionen A/B/C umgesetzt |
| 1 | 3 | Subagent (read-only Typechecker) | Typfehler aus Modul 2 gefunden & sauber behoben |
| 2 | 4 | MCP | `mcp_server.py` + `.mcp.json`: Codebasis als Werkzeug in Claude |
| 2 | 5 | Langzeitgedächtnis | `docs/ERKENNTNISSE.md` als persistentes Erkenntnis-Log |

**Didaktische Idee:** Jedes Modul hinterlässt einen sichtbaren, besseren Zustand.
Modul 3 „erntet" einen Fehler, den Modul 2 beim Implementieren erzeugt — so wird
der Nutzen eines spezialisierten Agenten unmittelbar erlebbar.

---

## Session 1

## Modul 0 — Setup & Überblick (15 min)

**Lernziel:** Umgebung steht, jede:r kann bauen, testen und ein erstes Bild erzeugen.

```bash
uv sync --extra dev          # .venv + magpylib, numpy, matplotlib, pytest, mypy
uv run pytest -q             # Tests grün (Feldtests benötigen magpylib)
uv run python - <<'PY'
import linmotor as lm
m = lm.example_motor(halbach=True)
print("Konsistenz:", m.consistency_issues() or "OK")
off = lm.find_commutation_offset(m)                 # einmalig nach Aufbau
f = lm.force(m, displacement_mm=2.0, theta_offset=off)
print(f"F = ({f.fx:.2f}, {f.fz:.2f}) N, |F| = {f.magnitude:.2f} N")
from linmotor.visualize import plot_motor
plot_motor(m, "motor.png", displacement_mm=2.0, theta_offset=off)
PY
```

**Physik in drei Sätzen für die Runde:**
Die Magnetbahn erzeugt ein in x periodisches Feld (`magpylib`). Der eisenlose
Läufer trägt 3-phasige Spulen; jeder Spulenschnitt wird in finite Volumen zerlegt,
und die Kraft ist das Integral `F = Σ (J × B)·dV` — ein Vektor in der x-z-Ebene
(Schub *und* Normalkraft). Weil die Spule fest steht und das **Magnet-Array
verschoben** wird, bestimmt man einmalig den Kommutierungsoffset (Phasenfindung)
und kommutiert dann synchron zur Verschiebung.

---

## Modul 1 — Arbeiten in der Codebasis (30 min)

**Lernziel:** Orientieren, gezielt ändern, Tests fahren, Diffs bewusst annehmen.
Verstehen, wofür `CLAUDE.md` da ist.

### 1.1 Projektgedächtnis aufbauen
```text
claude
```
```text
/init
```
`/init` analysiert das Repo und schlägt eine `CLAUDE.md` vor. Anschließend manuell
schärfen (das ist der eigentliche Lerneffekt):
```text
Ergänze CLAUDE.md knapp: (1) Koordinatensystem (x=Bewegung, z=Luftspalt,
y=Stromrichtung), (2) Einheiten-Konvention, (3) den Arbeitsablauf
„find_commutation_offset einmalig, dann force(...) mit Offset", (4) Befehl
`uv run pytest`. CLAUDE.md ist Kontext, kein Handbuch.
```

> **Merksatz:** `CLAUDE.md` wird bei jedem Start automatisch geladen — hier
> gehören langlebige Projektkonventionen hinein, keine Tagesnotizen.

### 1.2 Codebasis verstehen lassen
```text
Erkläre den Datenfluss von einem `Motor` bis zum Kraftvektor: Welche Funktion ruft
welche? Wie hängen Phasenfindung, Array-Verschiebung und Kommutierung zusammen?
Nutze die echten Dateinamen.
```

### 1.3 Kleine, echte Verbesserung
```text
Füge in force.py `peak_thrust(motor) -> float` hinzu: bestimme zuerst per
find_commutation_offset den Offset, dann das Maximum von thrust_curve über eine
elektrische Periode (Schrittweite 0.5 mm). Schreibe einen Test und lass
`uv run pytest` laufen.
```
Optionaler Quick-Win zum Abschluss: ein PNG erzeugen lassen
(`visualize.plot_motor`) — sichtbares Ergebnis der eigenen Arbeit.

**Zustand danach:** aussagekräftige `CLAUDE.md`, `peak_thrust()` inkl. Test.

---

## Modul 2 — Plan Mode: Feature-Baukasten (45–60 min)

**Lernziel:** Vor dem Coden erst einen Plan erzeugen, ihn **reviewen und editieren**,
dann ausführen — genau das, was bei mehrdateiigen Änderungen Fehler verhindert.

### 2.1 Plan Mode betreten
Drei Wege (einer reicht):
- **`Shift+Tab` zweimal** — Zyklus Default → Auto-Accept → **Plan**; Footer zeigt
  `⏸ plan mode on`.
- **`/plan`** als Slash-Command (plant nur den nächsten Turn).
- Session direkt im Plan Mode starten: `claude --permission-mode plan`.

> In Plan Mode ist Claude **hart read-only** — bis zur Plan-Freigabe wird nichts
> geschrieben oder ausgeführt.

### 2.2 Eine Aufgabe wählen
Die drei Optionen sind eigenständige Plan-Mode-Übungen auf der v0.2-Basis. Je nach
Zeit eine — oder zwei — auswählen. **Alle erweitern dieselbe Codebasis.**

#### Option A — Halbach-Array & Rippel-Vergleich
v0.2 enthält bereits ein *einfaches* segmentiertes Halbach. Diese Aufgabe lässt
sich zweifach fahren:
- **Geführte Nachimplementierung** (für Gruppen, die Halbach „von Hand" bauen
  wollen): die Logik sitzt in `geometry.magnet_layout`; als Referenz dienen.
- **Vertiefung** (empfohlen): die Analyse drumherum bauen.

Prompt in Plan Mode:
```text
Plane (noch nicht umsetzen): eine Funktion `compare_arrays(motor_std, motor_hal)
-> dict[str, float]`, die für beide Anordnungen per Phasenfindung kommutiert und
mittleren Schub sowie Rippel über eine elektrische Periode zurückgibt. 
Berücksichtige unsere Konventionen aus CLAUDE.md.
```

#### Option B — Mesh-Konvergenz der Finiten Volumen
Zeigt, dass die Kraft mit feinerer Diskretisierung konvergiert — und ab wann
weitere Zellen nichts mehr bringen.
```text
Plane (noch nicht umsetzen): `convergence_study(motor, cell_counts) -> dict[int,
float]`. Für jede Zellzahl n wird der Spulenquerschnitt auf n×n Zellen gesetzt
(dataclasses.replace, frozen!) und der Schub bei Verschiebung 0 mit *demselben*
einmalig gefundenen Offset berechnet. Plus ein Konvergenz-PNG. Tests inklusive.
```

#### Option C — Normalkraft- & Kraftwinkel-KPI
Nutzt den ohnehin berechneten F_z aus dem Kraftvektor.
```text
Plane (noch nicht umsetzen): `force_angle_deg(motor, displacement_mm, theta_offset)`
(= atan2(F_z, F_x)) und `normal_force_curve(...)`. Ergänze eine KPI-Funktion, die
über eine Periode die maximale Normalkraft und den mittleren Kraftwinkel liefert,
und visualisiere F_x und F_z gemeinsam. Tests inklusive.
```

### 2.3 Plan reviewen
Den Plan zur Freigabe **bewusst editieren** üben, z. B.:
```text
Ändere den Plan: lege die neue Funktion in force.py ab (nicht in einem neuen
Modul) und exportiere sie in __init__.py. Erst dann umsetzen.
```
Claude überarbeitet den Plan. **Erst dann** genehmigen — Claude wechselt in den
Ausführungsmodus und setzt um.

### 2.4 Ausführen & prüfen
```text
uv run pytest -q
```
und das Ergebnis sichtbar machen (Tabelle oder PNG).

> **Eingebauter Lehr-Effekt für Modul 3:** Beim Umsetzen schleicht sich häufig ein
> Annotations-Schnitzer ein — z. B. `convergence_study(...) -> float`, obwohl ein
> `dict` zurückkommt, oder `compare_arrays` liefert versehentlich eine `list`.
> **Nicht sofort korrigieren** — diesen Fehler fängt in Modul 3 der Typecheck-Agent.

**Zustand danach:** je nach Wahl `compare_arrays` / `convergence_study` /
`force_angle_deg` + Tests + PNG — mit einem latenten Typproblem.

---

## Modul 3 — Subagent: read-only Typechecker (30 min)

**Lernziel:** Einen spezialisierten Subagenten anlegen, dessen Werkzeuge auf
**Lesen** beschränkt sind. Er diagnostiziert, ändert aber nichts.

### 3.1 Agent anlegen
Interaktiv über `/agents` (von Anthropic empfohlen) — oder direkt die Datei
schreiben. Read-only heißt: nur `Read, Grep, Glob` plus `Bash` ausschließlich zum
Ausführen von `mypy`. **Kein** `Edit`/`Write`.

`.claude/agents/typechecker.md`:
```markdown
---
name: typechecker
description: >
  Prüft den Python-Code mit mypy auf Typfehler. NUR Diagnose, niemals Änderungen.
  Einsetzen nach Feature-Implementierungen oder vor einem Commit.
tools: Read, Grep, Glob, Bash
model: haiku
---
Du bist ein Typecheck-Spezialist für die Codebasis `linmotor`.

Aufgabe:
1. Führe `uv run mypy src` aus.
2. Fasse jede Meldung zusammen: Datei, Zeile, Kern des Problems.
3. Schlage pro Fund eine konkrete Korrektur vor — als Beschreibung, NICHT als Edit.

Strikte Regeln:
- Du veränderst NIEMALS Dateien (kein Edit/Write/MultiEdit).
- Mit Bash führst du ausschließlich `mypy`/`uv run mypy` aus, sonst nichts.
- Liegen keine Fehler vor, sage das klar und höre auf.
```

> **Warum `model: haiku`?** Read-only-Diagnose ist günstig und schnell — perfekt für
> einen häufig laufenden Helfer. Der eingebaute `Explore`-Agent ist aus demselben
> Grund read-only auf Haiku.

### 3.2 Agent benutzen
```text
Nutze den typechecker-Subagenten auf das gesamte Repo.
```
Er findet den Typfehler aus Modul 2 und **berichtet** nur. Der Haupt-Thread behebt
anschließend bewusst:
```text
Behebe den vom typechecker gemeldeten Typfehler und lass mypy erneut laufen.
```

**Zustand danach:** `mypy` sauber, ein wiederverwendbarer Diagnose-Agent im Repo
(`.claude/agents/typechecker.md`), versionierbar in Gitea.

---

## Session 2

*Details zum zweiten Teil (MCP-Server, komplexere Agenten) werden separat ausgearbeitet.*

## Modul 4 — MCP: die Codebasis als Werkzeug (45 min)

**Lernziel:** `linmotor` als MCP-Tools bereitstellen, sodass Claude den Motor
**selbst rechnen** kann. Der rote Faden schließt sich: aus der Bibliothek wird ein
Werkzeug.

### 4.1 Server schreiben
`FastMCP` aus dem offiziellen Python-SDK (`mcp`). Der Server importiert `linmotor`
und exponiert dünne Tool-Funktionen — inklusive Phasenfindung und vollem
Kraftvektor.

Prompt:
```text
Erstelle mcp_server.py mit FastMCP. Baue intern Motor/MagnetTrack/Forcer/CoilGeometry
und exponiere Tools, die linmotor nutzen:
- check_consistency(... Geometrieparameter ...) -> dict (Überlappung/Luftspalt)
- compute_force(... + air_gap, coil_width/height, halbach, displacement_mm ...)
  -> dict mit fx, fz, magnitude, force_angle_deg (Offset intern per Phasenfindung)
- motor_kpis(...) -> dict mit offset_deg, mean_thrust, peak_thrust, ripple, max_fz
stdio-Transport.
```
Referenzlösung siehe Anhang A.

### 4.2 In Claude Code registrieren (Projekt-Scope → `.mcp.json`)
```bash
claude mcp add linmotor --scope project -- uv run python mcp_server.py
```
Das schreibt eine versionierbare `.mcp.json` (Anhang B). Status prüfen:
```text
/mcp
```
Ausprobieren:
```text
Lege einen eisenlosen Motor mit Polteilung 10 mm, 14 Polen und 1,5 mm Luftspalt
aus. Prüfe zuerst die Konsistenz, dann vergleiche per MCP-Tool Standard gegen
Halbach (mean_thrust, ripple, max. Normalkraft) und empfiehl eine Variante.
```
Claude ruft jetzt die echte Codebasis auf statt zu schätzen.

### 4.3 Optional: Desktop-/Web-Client
Dieselbe Server-Definition funktioniert im Claude-Desktop-Client über dessen
`claude_desktop_config.json` (gleiches JSON-Format, anderer Ablageort).

> **Stolperstein:** Der `command` in `.mcp.json` muss vom Projektverzeichnis aus
> auflösbar sein. Claude Code setzt `CLAUDE_PROJECT_DIR`; mit `uv run` im
> Projektordner findet das SDK das Paket zuverlässig.

**Zustand danach:** `mcp_server.py` + `.mcp.json`. Die Codebasis ist als benanntes
Werkzeug `linmotor` in Claude eingebunden.

---

## Modul 5 — Langzeitgedächtnis (25 min)

**Lernziel:** Erkenntnisse **persistent** ablegen, getrennt von Tagescode.

### 5.1 Zwei Ebenen des Gedächtnisses
- **`CLAUDE.md`** — langlebige *Konventionen* (Einheiten, Tooling, Arbeitsablauf).
  Schnell ergänzen mit dem `#`-Präfix: eine mit `#` beginnende Zeile wird als
  Memory-Eintrag gespeichert.
- **`docs/ERKENNTNISSE.md`** — ein *Erkenntnis-Log*: datierte, fachliche Befunde
  aus Analysen. Wird aus `CLAUDE.md` heraus referenziert.

### 5.2 Referenz aus CLAUDE.md
```text
# Fachliche Auslegungs-Erkenntnisse stehen in docs/ERKENNTNISSE.md — vor
# Auslegungsfragen dort nachschlagen und neue Befunde dort ergänzen.
```

### 5.3 Befund festhalten
Den Befund aus der gewählten Modul-2-Aufgabe verstetigen, z. B.:
```text
Trage die Modul-2-Erkenntnis in docs/ERKENNTNISSE.md ein: Datum, Setup, Messwerte
(z. B. Rippel Standard vs. Halbach, oder ab welcher Zellzahl die Kraft konvergiert,
oder gemessene Normalkraft) und die Schlussfolgerung. Knapp und zitierfähig.
```

### 5.4 Test in neuer Session
```text
Ab welcher Finite-Volumen-Auflösung ist die Kraftberechnung praktisch konvergiert?
```
Claude liest `ERKENNTNISSE.md` und antwortet mit dem dokumentierten Befund statt
neu zu rechnen — sichtbarer Gewinn eines persistenten Gedächtnisses.

> **Abgrenzung:** `CLAUDE.md` = *wie wir arbeiten*. `ERKENNTNISSE.md` = *was wir
> herausgefunden haben*. Beides liegt im Repo, also teamweit und über Sessions hinweg.

**Zustand danach:** `docs/ERKENNTNISSE.md` mit erstem datiertem Befund, `CLAUDE.md`
verweist darauf.

---

## Abschluss / Transfer (10 min)
Von „Code lesen" → „planvoll erweitern" → „spezialisierte Agenten" → „persistentes
Wissen" → „eigenes Werkzeug". Dasselbe Muster trägt im PI-Alltag vom
Auslegungs-Skript bis zum hauseigenen MCP-Werkzeugkasten.

---
---

# Anhang — Referenzlösungen

> Für die Trainer:in. Empfehlung: einen gelösten Branch in Gitea vorhalten, um bei
> Bedarf live zu diffen. Alle Snippets wurden gegen v0.2 auf Lauffähigkeit geprüft.

## Anhang A — `mcp_server.py` (v0.2)

```python
"""MCP-Server: stellt die linmotor-Auslegung als Werkzeuge bereit (v0.2)."""

from __future__ import annotations

import math

from mcp.server.fastmcp import FastMCP

from linmotor import (
    CoilGeometry,
    Forcer,
    MagnetTrack,
    Motor,
    find_commutation_offset,
    force,
    ripple,
    thrust_curve,
)

mcp = FastMCP("linmotor")


def _build(
    pole_pitch_mm: float = 12.0,
    n_poles: int = 14,
    magnet_width_mm: float = 10.0,
    magnet_height_mm: float = 5.0,
    polarization_T: float = 1.3,
    air_gap_mm: float = 1.0,
    coil_width_mm: float = 3.0,
    coil_height_mm: float = 4.0,
    peak_current_A: float = 5.0,
    n_turns: int = 50,
    halbach: bool = False,
) -> Motor:
    track = MagnetTrack(
        pole_pitch_mm, n_poles, magnet_width_mm, magnet_height_mm,
        polarization_T=polarization_T, halbach=halbach,
    )
    forcer = Forcer(
        pole_pitch_mm=pole_pitch_mm,
        coil_z_mm=track.magnet_top_mm() + air_gap_mm + coil_height_mm / 2.0,
        coil=CoilGeometry(coil_width_mm, coil_height_mm),
        n_turns=n_turns,
        peak_current_A=peak_current_A,
    )
    return Motor(track, forcer)


def _period_samples(motor: Motor, offset: float) -> list[float]:
    xs = [0.5 * k for k in range(int(2 * motor.track.pole_pitch_mm / 0.5))]
    return thrust_curve(motor, xs, offset)


@mcp.tool()
def check_consistency(
    pole_pitch_mm: float = 12.0, n_poles: int = 14, magnet_width_mm: float = 10.0,
    magnet_height_mm: float = 5.0, air_gap_mm: float = 1.0,
    coil_width_mm: float = 3.0, coil_height_mm: float = 4.0, halbach: bool = False,
) -> dict[str, object]:
    """Geometrische Konsistenz prüfen (Spulenüberlappung, Luftspalt)."""
    motor = _build(
        pole_pitch_mm=pole_pitch_mm, n_poles=n_poles, magnet_width_mm=magnet_width_mm,
        magnet_height_mm=magnet_height_mm, air_gap_mm=air_gap_mm,
        coil_width_mm=coil_width_mm, coil_height_mm=coil_height_mm, halbach=halbach,
    )
    issues = motor.consistency_issues()
    return {"ok": not issues, "issues": issues}


@mcp.tool()
def compute_force(
    pole_pitch_mm: float = 12.0, n_poles: int = 14, magnet_width_mm: float = 10.0,
    magnet_height_mm: float = 5.0, polarization_T: float = 1.3, air_gap_mm: float = 1.0,
    coil_width_mm: float = 3.0, coil_height_mm: float = 4.0, peak_current_A: float = 5.0,
    n_turns: int = 50, halbach: bool = False, displacement_mm: float = 0.0,
) -> dict[str, float]:
    """Kraftvektor (fx, fz) bei gegebener Array-Verschiebung; Offset per Phasenfindung."""
    motor = _build(
        pole_pitch_mm, n_poles, magnet_width_mm, magnet_height_mm, polarization_T,
        air_gap_mm, coil_width_mm, coil_height_mm, peak_current_A, n_turns, halbach,
    )
    offset = find_commutation_offset(motor)
    f = force(motor, displacement_mm, offset)
    return {
        "fx": f.fx,
        "fz": f.fz,
        "magnitude": f.magnitude,
        "force_angle_deg": math.degrees(math.atan2(f.fz, f.fx)),
    }


@mcp.tool()
def motor_kpis(
    pole_pitch_mm: float = 12.0, n_poles: int = 14, magnet_width_mm: float = 10.0,
    magnet_height_mm: float = 5.0, polarization_T: float = 1.3, air_gap_mm: float = 1.0,
    coil_width_mm: float = 3.0, coil_height_mm: float = 4.0, peak_current_A: float = 5.0,
    n_turns: int = 50, halbach: bool = False,
) -> dict[str, float]:
    """Kennzahlen über eine elektrische Periode."""
    motor = _build(
        pole_pitch_mm, n_poles, magnet_width_mm, magnet_height_mm, polarization_T,
        air_gap_mm, coil_width_mm, coil_height_mm, peak_current_A, n_turns, halbach,
    )
    offset = find_commutation_offset(motor)
    fx = _period_samples(motor, offset)
    xs = [0.5 * k for k in range(len(fx))]
    fz = [abs(force(motor, x, offset).fz) for x in xs]
    return {
        "offset_deg": math.degrees(offset),
        "mean_thrust": sum(fx) / len(fx),
        "peak_thrust": max(fx),
        "ripple": ripple(fx),
        "max_normal_force": max(fz),
    }


if __name__ == "__main__":
    mcp.run()  # stdio-Transport
```

## Anhang B — `.mcp.json` (von `claude mcp add … --scope project` erzeugt)

```json
{
  "mcpServers": {
    "linmotor": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"]
    }
  }
}
```

## Anhang C — Modul-2-Referenzlösungen

Alle in `force.py` ablegen und in `__init__.py` exportieren.

**Option A — Halbach-Vergleich**
```python
def compare_arrays(motor_std: Motor, motor_hal: Motor) -> dict[str, float]:
    """Mittlerer Schub und Rippel für Standard- vs. Halbach-Anordnung."""
    xs = [0.5 * k for k in range(int(2 * motor_std.track.pole_pitch_mm / 0.5))]
    out: dict[str, float] = {}
    for name, motor in (("standard", motor_std), ("halbach", motor_hal)):
        offset = find_commutation_offset(motor)
        samples = thrust_curve(motor, xs, offset)
        out[f"{name}_mean"] = sum(samples) / len(samples)
        out[f"{name}_ripple"] = ripple(samples)
    return out
```
> Hinweis: Die eigentliche Halbach-Geometrie liegt in `geometry.magnet_layout`.
> Für die geführte Nachimplementierung dort ansetzen.

**Option B — Mesh-Konvergenz**
```python
from dataclasses import replace

def convergence_study(motor: Motor, cell_counts: list[int]) -> dict[int, float]:
    """Schub bei Verschiebung 0 für steigende Zellzahl (n x n), gleicher Offset."""
    offset = find_commutation_offset(motor)
    result: dict[int, float] = {}
    for n in cell_counts:
        coil = replace(motor.forcer.coil, n_cells_x=n, n_cells_z=n)
        m = Motor(motor.track, replace(motor.forcer, coil=coil))
        result[n] = thrust(m, 0.0, offset)
    return result
```

**Option C — Normalkraft / Kraftwinkel**
```python
import math

def force_angle_deg(motor: Motor, displacement_mm: float, theta_offset: float) -> float:
    """Winkel der Gesamtkraft in der x-z-Ebene (0° = reiner Schub)."""
    f = force(motor, displacement_mm, theta_offset)
    return math.degrees(math.atan2(f.fz, f.fx))

def normal_force_curve(
    motor: Motor, displacements_mm: list[float], theta_offset: float
) -> list[float]:
    """Normalkraft F_z über die Verschiebung."""
    return [force(motor, d, theta_offset).fz for d in displacements_mm]
```

## Anhang D — `docs/ERKENNTNISSE.md` (Startvorlage)

```markdown
# Auslegungs-Erkenntnisse (linmotor)

Datierte, fachliche Befunde aus Analysen. Vor Auslegungsfragen hier nachschlagen.

## 2025-… — <Thema der gewählten Modul-2-Aufgabe>
- Setup: example_motor(), identischer Spitzenstrom, eine elektrische Periode.
- Messwerte: …
- Schlussfolgerung: …
```

---

### Hinweis zur Erprobung
Der magpylib-abhängige Pfad (Feld/Kraft) wurde in der Erstellungsumgebung über
einen analytischen Stub geprüft (kein Netzwerk zum Installieren von magpylib); die
echten Feldwerte liefert magpylib bei euch. Geometrie-, Kommutierungs- und
Zeichenlogik sind direkt lauffähig. **Vor der Schulung einmal `uv sync --extra dev`
und `uv run pytest`** ausführen; magpylib ≥ 5 ist Voraussetzung (`polarization` in
Tesla, `getB` liefert Tesla).
