import os
import requests

L = "https://unpkg.com/leaflet@1.9.4/dist/"
DATEIEN = {
    "static/leaflet/leaflet.css": L + "leaflet.css",
    "static/leaflet/leaflet.js": L + "leaflet.js",
    "static/leaflet/images/marker-icon.png": L + "images/marker-icon.png",
    "static/leaflet/images/marker-icon-2x.png": L + "images/marker-icon-2x.png",
    "static/leaflet/images/marker-shadow.png": L + "images/marker-shadow.png",
    "static/leaflet/images/layers.png": L + "images/layers.png",
    "static/leaflet/images/layers-2x.png": L + "images/layers-2x.png",
    "static/chart.umd.js": "https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.js",
}

for pfad, url in DATEIEN.items():
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    antwort = requests.get(url, timeout=60)
    antwort.raise_for_status()
    with open(pfad, "wb") as datei:
        datei.write(antwort.content)
    print("geladen:", pfad)