import os
import sqlite3
import tempfile
import unittest

import auswertung
from suche import entfernung_km, stationen_fuer_ort, stationen_im_umkreis


class TestEntfernung(unittest.TestCase):
    def test_gleicher_punkt_ist_null(self):
        self.assertAlmostEqual(entfernung_km(51.0, 7.0, 51.0, 7.0), 0.0)

    def test_berlin_hamburg(self):
        d = entfernung_km(52.52, 13.405, 53.551, 9.994)
        self.assertTrue(250 < d < 260)


class TestUmkreis(unittest.TestCase):
    def test_iserlohn_findet_station(self):
        namen = [t[2] for t in stationen_im_umkreis(51.3755, 7.6957, 15)]
        self.assertIn("Iserlohn-Westig", namen)

    def test_mitten_im_atlantik_keine_station(self):
        self.assertEqual(stationen_im_umkreis(0.0, 0.0, 10), [])

    def test_fallback_nimmt_naechste_stationen(self):
        stationen, fallback = stationen_fuer_ort(0.0, 0.0, 10, "2000-01-01", "2005-12-31")
        self.assertTrue(fallback)
        self.assertEqual(len(stationen), 3)

    def test_kein_fallback_wenn_station_im_radius(self):
        stationen, fallback = stationen_fuer_ort(51.3755, 7.6957, 15, "2000-01-01", "2005-12-31")
        self.assertFalse(fallback)
        self.assertTrue(len(stationen) >= 1)


class TestAuswertung(unittest.TestCase):
    def setUp(self):
        self.datei = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.datei.close()
        self.alt = auswertung.DB_DATEI
        auswertung.DB_DATEI = self.datei.name
        v = sqlite3.connect(self.datei.name)
        v.execute("CREATE TABLE tageswert (stations_id INTEGER, datum TEXT, "
                  "tmk REAL, txk REAL, tnk REAL, rsk REAL, sdk REAL)")
        v.executemany("INSERT INTO tageswert VALUES (?,?,?,?,?,?,?)", [
            (1, "2020-01-01", 10.0, 12.0, 8.0, 2.0, None),
            (2, "2020-01-01", 20.0, 22.0, 18.0, 4.0, None),
            (1, "2020-01-02", 10.0, 11.0, 9.0, 1.0, None),
        ])
        v.commit()
        v.close()

    def tearDown(self):
        auswertung.DB_DATEI = self.alt
        os.remove(self.datei.name)

    def test_gleiche_entfernung_ergibt_normalen_mittelwert(self):
        stationen = [(10.0, 1), (10.0, 2)]
        zeilen = auswertung.auswerten(stationen, "2020-01-01", "2020-01-02", "tag")
        self.assertEqual(zeilen[0][1], 15.0)

    def test_naehere_station_zaehlt_mehr(self):
        stationen = [(1.0, 1), (2.0, 2)]   # Gewichte 1 und 0,25
        zeilen = auswertung.auswerten(stationen, "2020-01-01", "2020-01-02", "tag")
        self.assertEqual(zeilen[0][1], 12.0)   # (10*1 + 20*0,25) / 1,25
        self.assertEqual(zeilen[0][4], 2.4)

    def test_monat_summiert_niederschlag(self):
        stationen = [(10.0, 1), (10.0, 2)]
        zeilen = auswertung.auswerten(stationen, "2020-01-01", "2020-01-31", "monat")
        self.assertEqual(len(zeilen), 1)
        self.assertEqual(zeilen[0][1], 12.5)   # Tag 1: 15, Tag 2: 10
        self.assertEqual(zeilen[0][4], 4.0)    # 3.0 + 1.0


if __name__ == "__main__":
    unittest.main()