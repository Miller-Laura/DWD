import math
import sqlite3
from datenbank import DB_DATEI


def entfernung_km(breite1, laenge1, breite2, laenge2):
    """Entfernung zwischen zwei Koordinaten auf der Erdkugel (Haversine-Formel)."""
    r = 6371  # Erdradius in km
    phi1, phi2 = math.radians(breite1), math.radians(breite2)
    d_phi = math.radians(breite2 - breite1)
    d_lambda = math.radians(laenge2 - laenge1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _stationen_laden(von=None, bis=None):
    """Alle Stationen; mit von/bis nur die, deren Messzeitraum sich damit überschneidet."""
    sql = "SELECT stations_id, name, breite, laenge FROM station"
    parameter = []
    if von and bis:
        # Datum in der DB: JJJJMMTT, deshalb die Bindestriche weg
        sql += " WHERE von_datum <= ? AND bis_datum >= ?" #überschneidung prüfen, wenn der eine
# beginnt, bevor der andere endet, und umgekehrt.
        parameter = [bis.replace("-", ""), von.replace("-", "")]
    verbindung = sqlite3.connect(DB_DATEI)
    zeilen = verbindung.execute(sql, parameter).fetchall()
    verbindung.close()
    return zeilen


def stationen_im_umkreis(breite, laenge, radius_km, von=None, bis=None):
    treffer = []
    for stations_id, name, s_breite, s_laenge in _stationen_laden(von, bis):
        d = entfernung_km(breite, laenge, s_breite, s_laenge)
        if d <= radius_km:
            treffer.append((round(d, 1), stations_id, name, s_breite, s_laenge))
    treffer.sort()  # die am nähsten wird zuerst ausgewählt/genommen
    return treffer


def stationen_fuer_ort(breite, laenge, radius_km, von, bis, max_stationen=5, fallback_anzahl=3):
    """Gibt (Stationen, fallback) zurück.
    liegt keine der Stationen im Radius. Werden dieaußerhalb genommen (fallback=True)."""
    alle = sorted(
        (round(entfernung_km(breite, laenge, s_b, s_l), 1), sid, name, s_b, s_l)
        for sid, name, s_b, s_l in _stationen_laden(von, bis)
    )
    im_radius = [s for s in alle if s[0] <= radius_km]
    if im_radius:
        return im_radius[:max_stationen], False
    return alle[:fallback_anzahl], True


if __name__ == "__main__":
    print(stationen_im_umkreis(51.3755, 7.6957, 20))