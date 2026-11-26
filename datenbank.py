import sqlite3

DB_DATEI = "wetter.db"

def speichere_stationen(stationen):
    verbindung = sqlite3.connect(DB_DATEI)
    cursor = verbindung.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS station (
            stations_id INTEGER PRIMARY KEY,
            von_datum   TEXT,
            bis_datum   TEXT,
            hoehe       INTEGER,
            breite      REAL,
            laenge      REAL,
            name        TEXT,
            bundesland  TEXT,
            abgabe      TEXT
        )
    """)

    for s in stationen:
        cursor.execute(
            "INSERT OR REPLACE INTO station VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (s["id"], s["von_datum"], s["bis_datum"], s["hoehe"], s["breite"],
             s["laenge"], s["name"], s["bundesland"], s["abgabe"])
        )

    verbindung.commit()
    anzahl = cursor.execute("SELECT COUNT(*) FROM station").fetchone()[0]
    verbindung.close()
    print("Stationen in der DB:", anzahl)