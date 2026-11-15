"""Croiser une requête avec les sources et produire un rapport factuel.

Règle du projet : le rapport ne contient que des faits sourcés (quelle source,
quel lien, quelle date). Il ne qualifie jamais une entreprise et ne donne aucun
conseil. L'absence de résultat est dite comme telle, avec ses limites.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from .normalize import Requete, analyser, compacter, normaliser_domaine, normaliser_nom, strip_accents

DATA = Path(__file__).resolve().parent.parent / "data" / "amf_mises_en_garde.json"

AVERTISSEMENT = (
    "VérifCrypto QC rapporte ce que disent des sources publiques, à la date indiquée. "
    "Ce n'est ni un avis juridique ni un conseil financier. L'absence d'une entreprise "
    "dans ces listes ne prouve pas qu'elle est autorisée ou fiable."
)

# Liens officiels vérifiés, proposés selon le genre de requête
LIEN_REGISTRE_AMF = (
    "Registre des entreprises et des individus autorisés à exercer (AMF)",
    "https://lautorite.qc.ca/grand-public/registres/registre-des-entreprises-et-des-individus-autorises-a-exercer/",
)
LIEN_LISTE_AMF = ("Liste complète des mises en garde (AMF)", "https://lautorite.qc.ca/grand-public/salle-de-presse/mises-en-garde")
LIEN_CHECKFIRST = ("Vérifier l'inscription au Canada (ACVM, CheckFirst)", "https://www.checkfirst.ca/")
LIEN_FRAUDE_CRYPTO = (
    "Fraudes liées aux cryptoactifs (AMF, page en anglais)",
    "https://lautorite.qc.ca/en/general-public/fraud-prevention/types-of-fraud/cryptoasset-fraud",
)
LIEN_CHAINABUSE = ("Signalements publics d'adresses (Chainabuse) : chercher l'adresse", "https://www.chainabuse.com/")

MOTS_RECUPERATION = ("recuperation", "recovery", "recover", "recuperer", "remboursement")


@dataclass
class Constat:
    source: str
    titre: str
    url: str
    date: str
    correspondance: str  # ce qui a correspondu, et comment (exacte ou approximative)
    categories: list[str] = field(default_factory=list)


@dataclass
class Rapport:
    entree: str
    genre: str
    valeur: str
    sources_consultees: list[dict]
    constats: list[Constat]
    signaux: list[dict]
    liens_a_verifier: list[dict]
    avertissement: str = AVERTISSEMENT

    def to_dict(self) -> dict:
        return asdict(self)


def charger_amf(path: Path = DATA) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _domaines_entree(entree: dict) -> list[str]:
    out = []
    for site in entree.get("sites", []):
        d = normaliser_domaine(site)
        if d:
            out.append(d)
    return out


def _meme_domaine(requete: str, liste: str) -> bool:
    """Égal, ou sous-domaine l'un de l'autre (my.spxglobal.net ↔ spxglobal.net)."""
    return requete == liste or requete.endswith("." + liste) or liste.endswith("." + requete)


def chercher_amf(req: Requete, donnees: dict) -> list[Constat]:
    constats: list[Constat] = []
    for e in donnees["mises_en_garde"]:
        raison = None
        if req.genre == "site":
            for d in _domaines_entree(e):
                if _meme_domaine(req.valeur, d):
                    raison = f"site « {d} » inscrit dans la mise en garde"
                    break
        elif req.genre == "nom":
            noms = [e["nom"], *e.get("autres_noms", [])]
            for n in noms:
                nn = normaliser_nom(n)
                if nn and (nn == req.valeur or compacter(nn) == compacter(req.valeur)):
                    raison = f"nom « {n} » (correspondance exacte)"
                    break
            if raison is None:
                for n in noms:
                    nn = normaliser_nom(n)
                    if nn and len(req.valeur) >= 5 and SequenceMatcher(None, compacter(nn), compacter(req.valeur)).ratio() >= 0.88:
                        raison = f"nom « {n} » (correspondance approximative : vérifiez sur la fiche)"
                        break
        if raison:
            constats.append(
                Constat(
                    source="AMF – Mises en garde",
                    titre=f"Mise en garde à l'encontre de : {e['nom']}",
                    url=e["url"],
                    date=e["date_publication"],
                    correspondance=raison,
                    categories=list(e.get("categories", [])),
                )
            )
    return constats


def _signaux(req: Requete) -> list[dict]:
    texte = req.brut.lower()
    plain = strip_accents(texte)
    if any(m in plain for m in MOTS_RECUPERATION):
        return [
            {
                "fait": "L'entrée évoque la récupération de fonds. L'AMF a publié des mises en garde contre des "
                "services de « récupération » (par exemple « BNB (Service de récupération) », publiée le 26 juillet 2021).",
                "source": "AMF – Mises en garde",
                "url": "https://lautorite.qc.ca/en/general-public/media-centre/investor-warnings/investor-warnings-sheet/bnb-service-de-recuperation",
            }
        ]
    return []


def _liens(req: Requete) -> list[dict]:
    liens = [LIEN_LISTE_AMF]
    if req.genre in ("site", "nom"):
        liens += [LIEN_REGISTRE_AMF, LIEN_CHECKFIRST]
    else:
        liens += [LIEN_CHAINABUSE]
    liens.append(LIEN_FRAUDE_CRYPTO)
    return [{"titre": t, "url": u} for t, u in liens]


def verifier(texte: str, donnees: dict | None = None) -> Rapport:
    req = analyser(texte)
    donnees = donnees if donnees is not None else charger_amf()
    constats = chercher_amf(req, donnees) if req.genre in ("site", "nom") else []
    sources = [
        {
            "source": donnees["source"],
            "url": donnees["source_url"],
            "date_collecte": donnees["collecte"],
            "complet": donnees.get("complet", False),
            "nombre": len(donnees["mises_en_garde"]),
            "interrogee": req.genre in ("site", "nom"),
        }
    ]
    return Rapport(
        entree=req.brut,
        genre=req.genre,
        valeur=req.valeur,
        sources_consultees=sources,
        constats=constats,
        signaux=_signaux(req),
        liens_a_verifier=_liens(req),
    )
