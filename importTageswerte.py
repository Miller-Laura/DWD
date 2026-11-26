import csv
import io
import re
import sqlite3
import zipfile

import requests

from datenbank import DB_DATEI

BASIS = ("https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
         "climate/daily/kl/historical/")

_zip_namen = None


def zip_namen():
    """Verzeichnisliste einmal laden: {stations_id: dateiname}"""
    global _zip_namen
    if _zip_namen is None:
        html = requests.get(BASIS, timeout=60).text
        _zip_namen = {
            int(m.group(1)): m.group(0)
            for m in re.finditer(r"tageswerte_KL_(\d{5})_\d{8}_\d{8}_hist\.zip", html)
        }
    return _zip_namen


def zu_zahl(text):
    wert = float(text)
    return None if wert == -999 else wert      # -999 = Messwert fehlt


def lade_tageswerte(stations_id):
    name = zip_namen().get(stations_id)
    if name is None:
        return []
    antwort = requests.get(BASIS + name, timeout=120)
    antwort.raise_for_status()

    archiv = zipfile.ZipFile(io.BytesIO(antwort.content))
    produkt = next(n for n in archiv.namelist() if n.startswith("produkt_klima_tag"))
    text = archiv.read(produkt).decode("latin-1")

    zeilen = []
    for roh in csv.DictReader(io.StringIO(text), delimiter=";"): #datum wird auf bindestirchwe gesplitted
        z = {k.strip(): v.strip() for k, v in roh.items() if k}
        d = z["MESS_DATUM"]
        zeilen.append((
            stations_id, f"{d[:4]}-{d[4:6]}-{d[6:8]}",
            zu_zahl(z["TMK"]), zu_zahl(z["TXK"]), zu_zahl(z["TNK"]),
            zu_zahl(z["RSK"]), zu_zahl(z["SDK"]),
        ))
    return zeilen


def sorge_fuer_daten(stations_id):
    """Lädt die Tageswerte der Station, wenn noch nicht in der DB."""
    verbindung = sqlite3.connect(DB_DATEI)
    verbindung.execute("""
        CREATE TABLE IF NOT EXISTS tageswert (
            stations_id INTEGER, datum TEXT,
            tmk REAL, txk REAL, tnk REAL, rsk REAL, sdk REAL,
            PRIMARY KEY (stations_id, datum)
        )
    """)
    schon_da = verbindung.execute(
        "SELECT COUNT(*) FROM tageswert WHERE stations_id = ?", (stations_id,)
    ).fetchone()[0]
    if schon_da == 0:
        zeilen = lade_tageswerte(stations_id)
        verbindung.executemany(
            "INSERT OR REPLACE INTO tageswert VALUES (?, ?, ?, ?, ?, ?, ?)", zeilen # plathhalter gegen sqlinjection
        )
        verbindung.commit()
    verbindung.close()


if __name__ == "__main__":
    sorge_fuer_daten(2812)   # Testlauf, Stations-ID ggf. aus Tabelle nehmen