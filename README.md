startbefehl

uv run importAlle.py, uv run app.py

---

# Wetterprojekt: Auswertung historischer DWD-Wetterdaten

Webanwendung (Python, Flask, SQLite) zur Auswertung der Tageswerte des Deutschen Wetterdienstes
für beliebige Orte in Deutschland, als Tabelle, Diagramm und Karte.

## Starten

1. Abhängigkeiten stehen in `pyproject.toml` (`uv` installiert sie beim ersten Start).
2. Stationsliste laden: `uv run importStation.py`
3. Tageswerte laden (einmalig, dauert mehrere Stunden):
   - alle Stationen: `uv run importAlle.py`
   - nur ein Bundesland: `uv run importAlle.py Nordrhein-Westfalen`
   - bei Abbruch einfach neu starten, der Import macht an der Stelle weiter
4. Bibliotheken lokal ablegen (einmalig): `uv run lade_bibliotheken.py`
5. App starten: `uv run app.py`, dann im Browser `http://127.0.0.1:5000`
6. Tests: `uv run python -m unittest test_wetter -v`

## Aufbau (MVC)

| Teil | Dateien |
|---|---|
| Model (Daten und Berechnung) | `wetter.db` (SQLite), `datenbank.py`, `suche.py`, `auswertung.py` |
| View | `templates/index.html` (Formular, Karte, Diagramm, Tabelle) |
| Controller | `app.py` (Flask-Routen `/` und `/api/auswertung`) |
| Import | `importStation.py`, `importTageswerte.py`, `importAlle.py` |

## Ablauf einer Auswertung

1. Der Nutzer wählt Ort (oder Kartenklick), Zeitraum und Tag, Monat oder Jahr.
2. `app.py` prüft die Eingaben und bestimmt die Koordinaten (Nominatim oder Kartenklick).
3. `suche.py` wählt die Stationen im Umkreis (Haversine-Entfernung).
4. `auswertung.py` bildet pro Tag das nach Entfernung gewichtete Mittel
   und fasst dann per SQL nach Tag, Monat oder Jahr zusammen.
5. Die App liefert JSON, das Frontend zeichnet Tabelle, Diagramm und Karte.

## Anforderungen aus der Aufgabenstellung

- Tageswerte des DWD, in der Datenbank gespeichert (`importAlle.py`, `importTageswerte.py`)
- Auswertung von bis, auf Tages-, Monats- oder Jahresbasis
- Beliebiger Ort oder Adresse, benachbarte Stationen werden zusammengefasst
- Ergebnis als Tabelle und Grafik, zusätzlich als Karte

## Zusatzfunktionen

| Funktion | Beschreibung | Fundstelle |
|---|---|---|
| Gewichtetes Mittel | Nähere Stationen zählen stärker (Gewicht = 1 / Entfernung zum Quadrat), fehlende Messwerte werden nicht mitgezählt | `gewicht()`, `_gewichtetes_mittel()` in `auswertung.py` |
| Fallback auf Nachbarstationen | Liegt keine Station im Radius, werden die drei nächsten genutzt, die Oberfläche weist darauf hin | `stationen_fuer_ort()` in `suche.py` |
| Stationen nach Messzeitraum | Es werden nur Stationen berücksichtigt, die im gewählten Zeitraum Daten haben | `_stationen_laden()` in `suche.py` |
| Klimatrend | Lineare Regression (kleinste Quadrate), Trendlinie im Diagramm und Wert in °C pro Jahrzehnt, erst ab 10 Jahren Zeitspanne | `trend()` in `templates/index.html` |
| Messwert-Umschalter | Diagramm für Temperatur (Mittel, Maximum, Minimum), Niederschlag und Sonnenscheindauer | `zeigeDiagramm()` in `templates/index.html` |
| Zeitfenster nach Jahreszeit | Auswertung nur für Frühling, Sommer, Herbst oder Winter | `JAHRESZEITEN` in `app.py`, `_monatsfilter()` in `auswertung.py` |
| Farbige Stationskarte | Stationen nach Durchschnittstemperatur eingefärbt, Umkreis eingezeichnet | `farbe()`, `zeigeKarte()` in `templates/index.html` |
| CSV-Export | Die Ergebnistabelle lässt sich als CSV herunterladen | CSV-Block in `templates/index.html` |
| Daten vorab in der Datenbank | Alle Stationen importiert, Import mit Fortsetzen nach Abbruch | `importAlle.py` |
| Ortscache | Bereits gesuchte Orte werden gespeichert und funktionieren ohne Internet | `geocode()` in `app.py` |

## Qualitätssicherung

- Automatische Tests (`test_wetter.py`, 9 Tests): Entfernung, Umkreissuche, Fallback, Gewichtung, Zusammenfassung
- API-Tests mit Bruno (`bruno-sammlung`): Iserlohn Jahreswerte, Witten Heven Monatswerte,
  Kartenklick, Fallback, ungültiges Datum
- Abhärtung: SQL-Parameter statt String-Verkettung (Schutz vor SQL-Injection),
  Prüfung von Datum, Radius und Auswertungsart, Debug-Modus aus

## Bekannte Grenzen

- Die Ortssuche (Nominatim) und die Kartenkacheln brauchen Internet. Bereits gesuchte Orte gehen offline.
- Die Farbskala der Karte ist relativ: Blau und Rot beziehen sich auf die angezeigten Stationen.
- Der Klimatrend ist bei kurzen Zeiträumen nicht aussagekräftig und wird dort nicht berechnet.
- Die Datenbank ist sehr groß und wird deshalb nicht mit abgegeben, `importAlle.py` baut sie neu auf.