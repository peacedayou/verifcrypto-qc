"""Reconnaître et normaliser ce que l'utilisateur veut vérifier.

Trois genres d'entrées :
- un site Web (domaine ou adresse complète) ;
- une adresse de portefeuille (Ethereum et compatibles, Bitcoin) ;
- un nom d'entreprise ou de personne.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

EVM_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
BTC_RE = re.compile(r"^(bc1[02-9ac-hj-np-z]{11,71}|[13][1-9A-HJ-NP-Za-km-z]{25,34})$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")

# Formes juridiques retirées des noms avant comparaison
LEGAL_SUFFIXES = {
    "inc", "incorporated", "ltd", "ltee", "limited", "llc", "llp", "lp", "plc", "corp",
    "corporation", "co", "company", "sa", "sas", "sarl", "srl", "gmbh", "ag", "pte", "bv", "ou",
    "holding", "holdings", "group", "groupe",
}


@dataclass(frozen=True)
class Requete:
    brut: str
    genre: str  # "site", "adresse_evm", "adresse_btc" ou "nom"
    valeur: str  # forme normalisée


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normaliser_domaine(texte: str) -> str | None:
    """« https://WWW.Exemple.com/chemin?x=1 » → « exemple.com ». None si ce n'est pas un domaine."""
    t = texte.strip().strip(",;").lower()
    t = re.sub(r"^[a-z][a-z0-9+.-]*://", "", t)
    t = t.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    t = t.rsplit("@", 1)[-1].split(":", 1)[0].strip(".")
    if t.startswith("www."):
        t = t[4:]
    try:
        t = t.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    return t if DOMAIN_RE.match(t) else None


def normaliser_nom(texte: str) -> str:
    """« Gold Pride Holdings Ltée » → « gold pride »."""
    t = strip_accents(texte).lower()
    t = re.sub(r"\(.*?\)", " ", t)
    mots = re.findall(r"[a-z0-9]+", t)
    while mots and mots[-1] in LEGAL_SUFFIXES:
        mots.pop()
    return " ".join(mots)


def compacter(nom_normalise: str) -> str:
    """« gold pride » → « goldpride » : rapproche « Gold Pride » de « goldprideholdings »."""
    return nom_normalise.replace(" ", "")


def analyser(texte: str) -> Requete:
    brut = texte.strip()
    if not brut:
        raise ValueError("Entrée vide : indiquez un site, une adresse de portefeuille ou un nom.")
    if EVM_RE.match(brut):
        return Requete(brut, "adresse_evm", brut.lower())
    if BTC_RE.match(brut):
        return Requete(brut, "adresse_btc", brut)
    if " " not in brut or "://" in brut:
        domaine = normaliser_domaine(brut)
        if domaine:
            return Requete(brut, "site", domaine)
    nom = normaliser_nom(brut)
    if not nom:
        raise ValueError("Je ne reconnais ni un site, ni une adresse, ni un nom dans cette entrée.")
    return Requete(brut, "nom", nom)
