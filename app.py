import sqlite3
from datetime import date

import requests
from flask import Flask, jsonify, render_template, request

from auswertung import STUFEN, auswerten, stationswerte
from datenbank import DB_DATEI
from importTageswerte import sorge_fuer_daten
from suche import stationen_fuer_ort

app = Flask(__name__)

JAHRESZEITEN = {
    "fruehling": [3, 4, 5], "sommer": [6, 7, 8],
    "herbst": [9, 10, 11], "winter": [12, 1, 2],
}


def gueltiges_datum(text):
    try:
        date.fromisoformat(text)
        return True
    except ValueError:
        return False


def geocode(ort):
    """Ort -> (Breite, Länge). Gefundene Orte werden in der DB gespeichert (Ortscache)."""
    schluessel = ort.strip().lower()
    verbindung = sqlite3.connect(DB_DATEI)
    verbindung.execute("CREATE TABLE IF NOT EXISTS ortscache "
                       "(ort TEXT PRIMARY KEY, breite REAL, laenge REAL)")
    treffer = verbindung.execute(
        "SELECT breite, laenge FROM ortscache WHERE ort = ?", (schluessel,)).fetchone()
    if treffer:
        verbindung.close()
        return treffer

    try:
        antwort = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": ort, "format": "json", "limit": 1, "countrycodes": "de"},
            headers={"User-Agent": "wetterprojekt-schule/0.1"},
            timeout=15,
        )
        print("Nominatim:", antwort.status_code, antwort.text[:200])
        if antwort.status_code != 200:
            verbindung.close()
            return None
        gefunden = antwort.json()
    except (requests.RequestException, ValueError):
        verbindung.close()
        return None
    if not gefunden:
        verbindung.close()
        return None

    breite, laenge = float(gefunden[0]["lat"]), float(gefunden[0]["lon"])
    verbindung.execute("INSERT OR REPLACE INTO ortscache VALUES (?, ?, ?)",
                       (schluessel, breite, laenge))
    verbindung.commit()
    verbindung.close()
    return breite, laenge


@app.route("/")
def startseite():
    return render_template("index.html")


@app.route("/api/auswertung")
def api_auswertung():
    von = request.args.get("von", "")
    bis = request.args.get("bis", "")
    stufe = request.args.get("stufe", "jahr")
    monate = JAHRESZEITEN.get(request.args.get("zeitfenster", ""))

    try:
        radius = float(request.args.get("radius", 15))
    except ValueError:
        return jsonify(fehler="Der Umkreis muss eine Zahl sein."), 400
    radius = min(max(radius, 1), 100)

    if stufe not in STUFEN or not gueltiges_datum(von) or not gueltiges_datum(bis) or von > bis:
        return jsonify(fehler="Bitte einen gültigen Zeitraum und eine Auswertungsart angeben."), 400

    if request.args.get("lat") and request.args.get("lon"):
        try:
            breite, laenge = float(request.args["lat"]), float(request.args["lon"])
        except ValueError:
            return jsonify(fehler="Ungültige Koordinaten."), 400
    else:
        ort = request.args.get("ort", "").strip()
        if not ort:
            return jsonify(fehler="Bitte einen Ort eingeben oder auf die Karte klicken."), 400
        koordinaten = geocode(ort)
        if koordinaten is None:
            return jsonify(fehler="Ort nicht gefunden (oder keine Internetverbindung für die Ortssuche)."), 404
        breite, laenge = koordinaten

    stationen, fallback = stationen_fuer_ort(breite, laenge, radius, von, bis)
    if not stationen:
        return jsonify(fehler="Keine Wetterstation mit Daten im Zeitraum gefunden."), 404

    ids = [s[1] for s in stationen]
    for station_id in ids:
        try:
            sorge_fuer_daten(station_id)   # lädt nur nach, falls die Station noch fehlt
        except requests.RequestException:
            pass                           # offline: mit den vorhandenen Daten weiterarbeiten

    zeilen = auswerten(stationen, von, bis, stufe, monate)
    if not zeilen:
        return jsonify(fehler="Keine Messwerte im gewählten Zeitraum."), 404

    werte = stationswerte(ids, von, bis, monate)
    return jsonify(
        breite=breite, laenge=laenge, radius=radius, fallback=fallback,
        stationen=[{"km": s[0], "id": s[1], "name": s[2], "breite": s[3],
                    "laenge": s[4], "temp": werte.get(s[1])} for s in stationen],
        zeilen=zeilen,
    )


if __name__ == "__main__":
    app.run()