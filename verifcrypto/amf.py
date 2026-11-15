"""Collecte de la liste des mises en garde publiée par l'AMF.

Pages lues (relevé du 15 novembre 2026) :
- liste : https://lautorite.qc.ca/grand-public/salle-de-presse/mises-en-garde
  (20 fiches par page, pagination par le paramètre tx_solr[page]) ;
- fiche : .../mises-en-garde/fiche-mises-en-garde/<slug>, avec les classes
  misesengarde-title, search-result-date, news-list-category,
  news-list-websites et news-list-othernames.

Uniquement la bibliothèque standard. La collecte est polie : une requête à la fois,
avec une pause, et un User-Agent qui identifie le projet.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.request
from datetime import date
from pathlib import Path

BASE = "https://lautorite.qc.ca"
LISTE = BASE + "/grand-public/salle-de-presse/mises-en-garde"
FICHE = LISTE + "/fiche-mises-en-garde/"
USER_AGENT = "VerifCryptoQC/0.1 (+https://github.com/peacedayou/verifcrypto-qc)"

MOIS = {m: i for i, m in enumerate(
    ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"], 1)}

SLUG_RE = re.compile(r'href="[^"]*/fiche-mises-en-garde/([a-z0-9][a-z0-9-]*)')
PAGE_RE = re.compile(r"tx_solr%5Bpage%5D=(\d+)")


def slugs_de_liste(page_html: str) -> list[str]:
    vus, out = set(), []
    for s in SLUG_RE.findall(page_html):
        if s not in vus:
            vus.add(s)
            out.append(s)
    return out


def derniere_page(page_html: str) -> int:
    pages = [int(p) for p in PAGE_RE.findall(page_html)]
    return max(pages) if pages else 1


def date_iso(texte: str) -> str | None:
    m = re.search(r"(\d{1,2})(?:er)?\s+([a-zéû]+)\s+(\d{4})", texte.lower())
    if not m or m.group(2) not in MOIS:
        return None
    return f"{m.group(3)}-{MOIS[m.group(2)]:02d}-{int(m.group(1)):02d}"


def _texte(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _classe(nom: str) -> str:
    """Motif d'un attribut class qui contient « nom » parmi d'autres classes."""
    return r'class="(?:[^"]*\s)?' + re.escape(nom) + r'(?:\s[^"]*)?"'


def lire_fiche(slug: str, fiche_html: str) -> dict | None:
    debut = fiche_html.find("news-single-misesengarde")
    if debut < 0:
        return None
    fin = fiche_html.find("TYPO3SEARCH_end", debut)
    zone = fiche_html[debut : fin if fin > 0 else None]
    m_nom = re.search(r"<h2[^>]*" + _classe("misesengarde-title") + r"[^>]*>(.*?)</h2>", zone, re.S)
    if not m_nom:
        return None
    m_date = re.search(r"<div[^>]*" + _classe("search-result-date") + r"[^>]*>(.*?)</div>", zone, re.S)
    categories = [_texte(x) for x in re.findall(r"<span[^>]*" + _classe("news-list-category") + r"[^>]*>(.*?)</span>", zone, re.S)]

    def items(ul_classe: str) -> list[str]:
        m = re.search(r"<ul[^>]*" + _classe(ul_classe) + r"[^>]*>(.*?)</ul>", zone, re.S)
        return [_texte(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", m.group(1), re.S)] if m else []

    sites = []
    for s in items("news-list-websites"):
        sites += [x for x in re.split(r"[,\s]+", s) if x]
    return {
        "slug": slug,
        "nom": _texte(m_nom.group(1)),
        "date_publication": date_iso(_texte(m_date.group(1))) if m_date else None,
        "categories": [c for c in categories if c],
        "sites": sites,
        "autres_noms": [x for x in items("news-list-othernames") if x],
        "url": FICHE + slug,
    }


def _get(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-CA,fr"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (URL fixe vers l'AMF)
        return r.read().decode("utf-8", errors="replace")


def collecter(pause: float = 0.5, max_pages: int | None = None, get=_get, log=print) -> dict:
    premiere = get(LISTE)
    total = derniere_page(premiere)
    if max_pages:
        total = min(total, max_pages)
    slugs = slugs_de_liste(premiere)
    for page in range(2, total + 1):
        time.sleep(pause)
        slugs += [s for s in slugs_de_liste(get(f"{LISTE}?tx_solr%5Bcontroller%5D=Search&tx_solr%5Bpage%5D={page}")) if s not in slugs]
    log(f"{len(slugs)} fiches sur {total} page(s)")
    fiches, erreurs = [], 0
    for i, slug in enumerate(slugs, 1):
        time.sleep(pause)
        try:
            f = lire_fiche(slug, get(FICHE + slug))
        except Exception as exc:  # une fiche en erreur ne bloque pas la collecte
            erreurs += 1
            log(f"  erreur sur {slug} : {exc}")
            continue
        if f:
            fiches.append(f)
        if i % 100 == 0:
            log(f"  {i}/{len(slugs)}")
    if not fiches:
        raise RuntimeError("Aucune fiche lue : la structure des pages de l'AMF a peut-être changé.")
    return {
        "source": "Autorité des marchés financiers (Québec) – Mises en garde",
        "source_url": LISTE,
        "collecte": date.today().isoformat(),
        "complet": max_pages is None and erreurs == 0,
        "note": f"{len(fiches)} fiches lues, {erreurs} en erreur.",
        "mises_en_garde": fiches,
    }


def enregistrer(donnees: dict, chemin: Path) -> None:
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
