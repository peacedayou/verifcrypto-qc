"""Mise en forme du rapport en français (texte et Markdown)."""

from __future__ import annotations

from .verifier import Rapport

GENRES = {
    "site": "site Web",
    "adresse_evm": "adresse de portefeuille (Ethereum ou compatible)",
    "adresse_btc": "adresse de portefeuille (Bitcoin)",
    "nom": "nom d'entreprise ou de personne",
}

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def date_fr(iso: str) -> str:
    a, m, j = iso.split("-")
    jour = int(j)
    return f"{'1er' if jour == 1 else jour} {MOIS[int(m) - 1]} {a}"


def en_texte(r: Rapport) -> str:
    lignes = [f"Vérification de : {r.entree}", f"Reconnu comme : {GENRES[r.genre]} ({r.valeur})", ""]
    src = r.sources_consultees[0]
    if src["interrogee"]:
        portee = "liste complète" if src["complet"] else f"échantillon de {src['nombre']} fiches"
        lignes.append(f"Source consultée : {src['source']} ({portee}, données du {date_fr(src['date_collecte'])})")
    else:
        lignes.append("Les mises en garde de l'AMF visent des sites et des entreprises, pas des adresses de portefeuille.")
    lignes.append("")
    if r.constats:
        lignes.append(f"Résultats : {len(r.constats)} mention(s) trouvée(s)")
        for c in r.constats:
            lignes += [
                f"  • {c.titre}",
                f"    Publiée le {date_fr(c.date)} — {', '.join(c.categories) or 'sans catégorie'}",
                f"    Correspondance : {c.correspondance}",
                f"    Fiche : {c.url}",
            ]
    elif src["interrogee"]:
        lignes.append("Résultats : aucune mention dans la source consultée.")
    for s in r.signaux:
        lignes += ["", f"À savoir : {s['fait']}", f"  Source : {s['url']}"]
    lignes += ["", "Pour aller plus loin :"]
    lignes += [f"  • {lien['titre']} : {lien['url']}" for lien in r.liens_a_verifier]
    lignes += ["", r.avertissement]
    return "\n".join(lignes)
