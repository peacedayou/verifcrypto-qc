import json
import unittest
from pathlib import Path

from verifcrypto import amf
from verifcrypto.__main__ import main
from verifcrypto.normalize import analyser
from verifcrypto.rapport import en_texte
from verifcrypto.verifier import charger_amf, verifier

ICI = Path(__file__).parent
V = json.loads((ICI / "vecteurs.json").read_text(encoding="utf-8"))
DONNEES = charger_amf()


class Analyse(unittest.TestCase):
    def test_vecteurs(self):
        for entree, genre, valeur in V["analyser"]:
            with self.subTest(entree=entree):
                r = analyser(entree)
                self.assertEqual((r.genre, r.valeur), (genre, valeur))

    def test_entree_vide(self):
        with self.assertRaises(ValueError):
            analyser("   ")


class Recherche(unittest.TestCase):
    def test_vecteurs(self):
        for entree, slugs in V["chercher"]:
            with self.subTest(entree=entree):
                r = verifier(entree, DONNEES)
                self.assertEqual([c.url.rsplit("/", 1)[1] for c in r.constats], slugs)

    def test_recuperation(self):
        for entree, attendu in V["recuperation"]:
            with self.subTest(entree=entree):
                self.assertEqual(bool(verifier(entree, DONNEES).signaux), attendu)

    def test_adresse_ne_consulte_pas_l_amf(self):
        r = verifier("0x52908400098527886E0F7030069857D2E4169EE7", DONNEES)
        self.assertEqual(r.constats, [])
        self.assertFalse(r.sources_consultees[0]["interrogee"])
        self.assertIn("chainabuse", " ".join(l["url"] for l in r.liens_a_verifier))

    def test_chaque_constat_est_source_et_date(self):
        for e in DONNEES["mises_en_garde"]:
            r = verifier(e["sites"][0], DONNEES)
            self.assertTrue(r.constats, e["slug"])
            for c in r.constats:
                self.assertTrue(c.url.startswith("https://lautorite.qc.ca/"))
                self.assertRegex(c.date, r"^\d{4}-\d{2}-\d{2}$")


class Rapport(unittest.TestCase):
    MOTS_INTERDITS = ("arnaque", "fraudeur", "escroc", "investissez", "achetez", "vendez", "rendement garanti", "sûr à 100")

    def test_rapport_factuel_sans_conseil(self):
        for entree in ("f24group.com", "exemple.com", "Gold Pride", "0x52908400098527886E0F7030069857D2E4169EE7"):
            t = en_texte(verifier(entree, DONNEES)).lower()
            for mot in self.MOTS_INTERDITS:
                self.assertNotIn(mot, t, (entree, mot))
            self.assertIn("ni un avis juridique ni un conseil financier", t)

    def test_absence_dite_avec_ses_limites(self):
        t = en_texte(verifier("exemple.com", DONNEES))
        self.assertIn("aucune mention", t)
        self.assertIn("ne prouve pas", t)

    def test_cli(self):
        self.assertEqual(main(["--json", "f24group.com"]), 0)
        self.assertEqual(main([""]), 2)


class CollecteAMF(unittest.TestCase):
    def test_fiche(self):
        f = amf.lire_fiche("gold-pride-holdings", (ICI / "fixtures" / "fiche.html").read_text(encoding="utf-8"))
        self.assertEqual(f["nom"], "Gold Pride Holdings")
        self.assertEqual(f["date_publication"], "2026-10-22")
        self.assertEqual(f["categories"], ["Cryptoactifs", "Plateforme à haut risque"])
        self.assertEqual(f["sites"], ["goldprideholdings.net", "goldprideholdings.com"])
        self.assertEqual(f["autres_noms"], ["goldprideholdings"])

    def test_fiche_hors_structure(self):
        self.assertIsNone(amf.lire_fiche("x", "<html><body>Page introuvable</body></html>"))

    def test_liste(self):
        h = (ICI / "fixtures" / "liste.html").read_text(encoding="utf-8")
        self.assertEqual(amf.slugs_de_liste(h), ["f24group", "royalispower"])
        self.assertEqual(amf.derniere_page(h), 71)

    def test_dates(self):
        self.assertEqual(amf.date_iso("Publication : 1er juillet 2021"), "2021-07-01")
        self.assertEqual(amf.date_iso("6 décembre 2026"), "2026-12-06")
        self.assertIsNone(amf.date_iso("bientôt"))

    def test_collecte_complete_avec_faux_reseau(self):
        liste = (ICI / "fixtures" / "liste.html").read_text(encoding="utf-8")
        fiche = (ICI / "fixtures" / "fiche.html").read_text(encoding="utf-8")

        def get(url):
            return fiche if "/fiche-mises-en-garde/" in url else liste

        d = amf.collecter(pause=0, max_pages=2, get=get, log=lambda *_: None)
        self.assertEqual(len(d["mises_en_garde"]), 2)
        self.assertFalse(d["complet"])  # pages limitées

    def test_structure_changee_fait_echouer(self):
        with self.assertRaises(RuntimeError):
            amf.collecter(pause=0, get=lambda url: "<html></html>", log=lambda *_: None)


class Donnees(unittest.TestCase):
    def test_instantane_valide(self):
        self.assertTrue(DONNEES["mises_en_garde"])
        for e in DONNEES["mises_en_garde"]:
            self.assertTrue(e["url"].endswith("/" + e["slug"]))
            self.assertRegex(e["date_publication"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
