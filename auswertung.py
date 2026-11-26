import sqlite3
from datenbank import DB_DATEI

STUFEN = {"tag": 10, "monat": 7, "jahr": 4} #dictionary üfr zuordnung


def _monatsfilter(monate):
    if not monate:
        return "", []
    platzhalter = ",".join("?" * len(monate))
    return f" AND CAST(substr(datum, 6, 2) AS INTEGER) IN ({platzhalter})", list(monate)


def _gewichtetes_mittel(spalte):
    """Gewichtetes Mittel; fehlende Werte (NULL) zählen mit ihrem Gewicht nicht mit."""
    return (f"SUM(t.{spalte} * g.w) / "
            f"SUM(CASE WHEN t.{spalte} IS NOT NULL THEN g.w END)")


def gewicht(entfernung_km):
    """Näher = wichtiger: 1 / Entfernung zum Quadrat (mindestens 0,5 km, gegen Division durch 0)."""
    return 1.0 / max(entfernung_km, 0.5) ** 2


def auswerten(stationen, von, bis, stufe, monate=None):
    """stationen: Liste von Tupeln (entfernung_km, stations_id, ...)"""
    n = STUFEN[stufe]
    gewichte = []
    for s in stationen:
        gewichte += [s[1], gewicht(s[0])]
    werte_sql = ",".join("(?, ?)" for _ in stationen)
    filter_sql, filter_werte = _monatsfilter(monate)

    sql = f"""
        WITH g(stations_id, w) AS (VALUES {werte_sql}),
        tag AS (
            SELECT t.datum AS datum,
                   {_gewichtetes_mittel('tmk')} AS tmk,
                   {_gewichtetes_mittel('txk')} AS txk,
                   {_gewichtetes_mittel('tnk')} AS tnk,
                   {_gewichtetes_mittel('rsk')} AS rsk,
                   {_gewichtetes_mittel('sdk')} AS sdk
            FROM tageswert t JOIN g ON g.stations_id = t.stations_id
            WHERE t.datum BETWEEN ? AND ?{filter_sql}
            GROUP BY t.datum
        )
        SELECT substr(datum, 1, {n}) AS zeitraum,
               ROUND(AVG(tmk), 1), ROUND(MAX(txk), 1), ROUND(MIN(tnk), 1),
               ROUND(SUM(rsk), 1), ROUND(SUM(sdk), 1)
        FROM tag
        GROUP BY zeitraum
        ORDER BY zeitraum
    """
    verbindung = sqlite3.connect(DB_DATEI)
    ergebnis = verbindung.execute(sql, [*gewichte, von, bis, *filter_werte]).fetchall()
    verbindung.close()
    return ergebnis


def stationswerte(stations_ids, von, bis, monate=None):
    """Durchschnittstemperatur je Station (für die farbige Karte)."""
    platzhalter = ",".join("?" * len(stations_ids))
    filter_sql, filter_werte = _monatsfilter(monate)
    verbindung = sqlite3.connect(DB_DATEI)
    zeilen = verbindung.execute(
        f"""SELECT stations_id, ROUND(AVG(tmk), 1) FROM tageswert
            WHERE stations_id IN ({platzhalter}) AND datum BETWEEN ? AND ?{filter_sql}
            GROUP BY stations_id""",
        [*stations_ids, von, bis, *filter_werte],
    ).fetchall()
    verbindung.close()
    return dict(zeilen)