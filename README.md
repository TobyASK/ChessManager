# Centre Échecs

Application Python 3.10+ hors ligne, conforme au modèle MVC, pour la gestion de joueurs et de tournois d'échecs.

## Lancement

```bash
python app.py
```

## Installer l'environnement Python

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Générer le rapport PEP 8

```bash
flake8 --format=html --htmldir=flake8_rapport
```

Le dossier `flake8_rapport` contient le rapport HTML de conformité PEP 8 (aucune erreur attendue).

## Structure du projet

- **modèles** : `models/` (Player, Tournament, Round)
- **vues** : `views/` (menus, affichage, rapports)
- **contrôleurs** : `controllers/` (gestion logique)
- **persistance** : `storage/json_store.py` (sauvegarde/chargement JSON)
- **utilitaires** : `utils/` (validators, pairing)
- **données** : `data/players.json`, `data/tournaments/tournaments.json`

## Fonctionnalités principales

- Gestion des joueurs (ajout, liste alphabétique, identifiant national unique)
- Gestion des tournois (création, inscription, déroulement, résultats)
- Appariements automatiques selon le score et l'historique des rencontres
- Rapports textuels sur les joueurs et tournois
- Sauvegarde/chargement automatique des données après chaque modification

## Spécifications techniques

- Python 3.10+
- Respect du modèle MVC
- Persistance via fichiers JSON
- Conformité PEP 8 (max-line-length: 119)
- Rapport flake8 généré dans `flake8_rapport/`

[Anis Bekkouche](https://github.com/TobyASK)
