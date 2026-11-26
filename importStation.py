from datenbank import speichere_stationen
import re
import requests

URL = ("https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
       "climate/daily/kl/historical/KL_Tageswerte_Beschreibung_Stationen.txt")

def lade_stationsdatei():
    antwort = requests.get(URL, timeout=30)
    antwort.raise_for_status()
    text = antwort.content.decode("latin-1") #dwd speichert es so
    return text.splitlines()

zeilen = lade_stationsdatei()
for z in zeilen[:5]:
    print(z)
print("Anzahl Zeilen:", len(zeilen))

def parse_station(zeile):
    teile = zeile.split(maxsplit=6)
    # [0] - [5]: ID, von, bis, Höhe, Breite, Länge aufteilung
    # [6]: Rest -> "Aachen        Nordrhein-Westfalen        Frei"

    station = {
        "id": int(teile[0]), "von_datum": teile[1], "bis_datum": teile[2],
        "hoehe": int(teile[3]), "breite": float(teile[4]), "laenge": float(teile[5])
    }

    rest = teile[6]
    rest_teile = re.split(r"\s{2,}", rest.strip()) #2 leerzeichen
    station["name"] = rest_teile[0]
    station["bundesland"] = rest_teile[1]


    if len(rest_teile) == 3:
        station["abgabe"] = rest_teile[2]
    else:
        station["abgabe"] = ""

    return station

stationen = []
for zeile in zeilen[2:]:
    if zeile.strip():
        stationen.append(parse_station(zeile))

speichere_stationen(stationen)

