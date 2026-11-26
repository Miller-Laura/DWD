import sqlite3
import sys
import time
import zipfile
import requests

from datenbank import DB_DATEI
from importTageswerte import zip_namen, lade_tageswerte


def lege_tabellen_an(verbindung):
    verbindung.execute("""
        CREATE TABLE IF NOT EXISTS tageswert (
            stations_id INTEGER, datum TEXT,
            tmk REAL, txk REAL, tnk REAL, rsk REAL, sdk REAL,
            PRIMARY KEY (stations_id, datum)
        )
    """)
    verbindung.execute("""
        CREATE TABLE IF NOT EXISTS importiert (
            stations_id INTEGER PRIMARY KEY,
            anzahl INTEGER,
            zeitpunkt TEXT
        )
    """)


def importiere_alle(bundesland=None):
    verbindung = sqlite3.connect(DB_DATEI)
    lege_tabellen_an(verbindung)

    sql = "SELECT stations_id, name FROM station"
    parameter = []
    if bundesland:
        sql += " WHERE bundesland = ?"
        parameter.append(bundesland)
    stationen = verbindung.execute(sql, parameter).fetchall()

    verfuegbar = zip_namen()   # Stationen, from DWD with ZIP
    fertig = {z[0] for z in verbindung.execute("SELECT stations_id FROM importiert")}
    fertig |= {z[0] for z in verbindung.execute("SELECT DISTINCT stations_id FROM tageswert")}

    offen = [(i, n) for i, n in stationen if i in verfuegbar and i not in fertig]
    print(f"{len(offen)} Stationen noch zu laden ({len(fertig)} schon vorhanden)")

    start = time.time()
    for nr, (stations_id, name) in enumerate(offen, start=1):
        zeilen = None
        for versuch in range(3):
            try:
                zeilen = lade_tageswerte(stations_id)
                break
            except (requests.RequestException, zipfile.BadZipFile) as fehler:
                print(f"  Fehler bei {name}: {fehler} (Versuch {versuch + 1}/3)")
                time.sleep(5)
        if zeilen is None:
            print(f"  {name} übersprungen")
            continue

        verbindung.executemany(
            "INSERT OR REPLACE INTO tageswert VALUES (?, ?, ?, ?, ?, ?, ?)", zeilen)
        verbindung.execute(
            "INSERT OR REPLACE INTO importiert VALUES (?, ?, datetime('now'))",
            (stations_id, len(zeilen)))
        verbindung.commit()   # pro Station: entweder ganz drin oder gar nicht

        pro_station = (time.time() - start) / nr
        rest_min = pro_station * (len(offen) - nr) / 60
        print(f"[{nr}/{len(offen)}] {name}: {len(zeilen)} Tage, noch ca. {rest_min:.0f} Min.")

    verbindung.close()
    print("Fertig.")


if __name__ == "__main__":
    # Aufruf:  uv run importAlle.py                       -> alle Stationen
    #          uv run importAlle.py Nordrhein-Westfalen   -> nur ein Bundesland
    importiere_alle(sys.argv[1] if len(sys.argv) > 1 else None)