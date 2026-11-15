# VérifCrypto QC

[![CI](https://github.com/peacedayou/verifcrypto-qc/actions/workflows/ci.yml/badge.svg)](https://github.com/peacedayou/verifcrypto-qc/actions/workflows/ci.yml)

Vérifiez **en français** un site Web, une adresse de portefeuille ou le nom d'une entreprise
avant d'envoyer de l'argent. VérifCrypto QC croise votre recherche avec les **mises en garde
de l'Autorité des marchés financiers (AMF)** et vous donne les liens officiels pour vérifier
une inscription.

**Démo :** https://peacedayou.github.io/verifcrypto-qc/

## Le principe : des faits sourcés, jamais de conseil

- Chaque résultat cite sa **source**, son **lien** et sa **date** de publication.
- L'outil ne qualifie personne (pas de « arnaque », pas de « fiable ») : il dit ce que la
  source publie, et ce qui a correspondu (site exact, sous-domaine, nom exact ou approximatif).
- L'absence de résultat est dite avec ses limites : ne pas figurer sur une liste ne prouve
  pas qu'une entreprise est autorisée.
- Une recherche qui évoque la **récupération de fonds** rappelle que l'AMF a publié des
  mises en garde contre ce type de service (les victimes sont souvent sollicitées une
  deuxième fois).
- Aucun compte, aucune donnée personnelle conservée, aucun jeton, aucune promesse de rendement.

## Utilisation

```bash
python -m verifcrypto "https://my.spxglobal.net"
python -m verifcrypto "Gold Pride Holdings"
python -m verifcrypto --json "0x52908400098527886E0F7030069857D2E4169EE7"
```

Aucune bibliothèque à installer : Python 3.10 ou plus récent.

## Sources

| Source | Utilisation | Mise à jour |
| --- | --- | --- |
| [AMF – Mises en garde](https://lautorite.qc.ca/grand-public/salle-de-presse/mises-en-garde) | Comparaison des sites et des noms (y compris les « autres noms d'affaires ») | Chaque lundi, par GitHub Actions |
| [Registre de l'AMF](https://lautorite.qc.ca/grand-public/registres/registre-des-entreprises-et-des-individus-autorises-a-exercer/) | Lien pour vérifier une inscription au Québec | — |
| [CheckFirst (ACVM)](https://www.checkfirst.ca/) | Lien pour vérifier une inscription au Canada | — |
| [Chainabuse](https://www.chainabuse.com/) | Lien vers les signalements publics d'adresses | — |

Le dépôt contient au départ un **échantillon réel** des 20 mises en garde les plus récentes
(relevé du 15 novembre 2026). La tâche planifiée `Données et démo` le remplace chaque semaine
par la liste complète (environ 1 400 fiches), avec une pause entre chaque requête pour ne pas
surcharger le site de l'AMF. Si la structure des pages change, la collecte échoue au lieu
de publier des données vides.

## Développement

```bash
python -m unittest discover -s tests -v   # tests Python, sans réseau
node --test tests/verif.test.mjs          # tests de la page Web
python -m verifcrypto maj                 # collecte réelle (réseau requis)
```

La page Web (`web/`) reprend la même logique en JavaScript ; les deux versions sont testées
avec les mêmes vecteurs (`tests/vecteurs.json`) pour donner exactement les mêmes réponses.

```
verifcrypto/normalize.py   reconnaissance et normalisation (site, adresse, nom)
verifcrypto/verifier.py    comparaison avec les sources, rapport structuré
verifcrypto/rapport.py     rapport en français
verifcrypto/amf.py         collecte de la liste de l'AMF
web/                       page de démonstration (GitHub Pages)
```

## Avertissement

VérifCrypto QC rapporte ce que disent des sources publiques, à la date indiquée. Ce n'est ni
un avis juridique ni un conseil financier. En cas de doute, communiquez avec le centre
d'information de l'AMF.

## Licence

MIT
