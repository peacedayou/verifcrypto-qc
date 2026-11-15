"""Ligne de commande.

    python -m verifcrypto "exemple.com"
    python -m verifcrypto --json "Nom de l'entreprise"
    python -m verifcrypto maj            # met à jour les données de l'AMF (réseau requis)
"""

from __future__ import annotations

import argparse
import json
import sys

from . import amf
from .rapport import en_texte
from .verifier import DATA, verifier


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="verifcrypto", description="Vérifie un site, une adresse ou une entreprise contre des sources publiques québécoises et canadiennes.")
    p.add_argument("entree", help="site, adresse de portefeuille ou nom ; « maj » pour mettre à jour les données")
    p.add_argument("--json", action="store_true", help="rapport au format JSON")
    p.add_argument("--max-pages", type=int, default=None, help="(maj) limite le nombre de pages lues")
    a = p.parse_args(argv)

    if a.entree == "maj":
        donnees = amf.collecter(max_pages=a.max_pages)
        amf.enregistrer(donnees, DATA)
        print(f"{len(donnees['mises_en_garde'])} mises en garde enregistrées dans {DATA}")
        return 0
    try:
        r = verifier(a.entree)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2) if a.json else en_texte(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
