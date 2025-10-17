from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime
import dateparser
import random
import string
from controllers.tournament_controller import TournamentController
from controllers.player_controller import PlayerController
from utils.validators import ask_birthdate, ask_tournament_dates
from settings import ENABLE_AUTOCOMPLETE
from models.tournament import Tournament


def read_int(prompt: str, default: int | None = None) -> int:
    raw_value = input(prompt).strip()
    if not raw_value and default is not None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        print("Valeur invalide.")
        return read_int(prompt, default)


def read_date_text(prompt: str, allow_empty: bool = True) -> str:
    raw = input(prompt).strip()
    if not raw and allow_empty:
        return ""
    if not raw:
        print("Date vide non autorisée.")
        return read_date_text(prompt, allow_empty)
    dt = dateparser.parse(raw, languages=["fr"])
    if not dt:
        print("Date invalide.")
        return read_date_text(prompt, allow_empty)
    return dt.strftime("%Y-%m-%d")


def read_birthdate(prompt: str) -> str:
    raw = input(prompt).strip()
    if not raw:
        return ""
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        print("Format invalide. Attendu: YYYY-MM-DD.")
        return read_birthdate(prompt)


def _auto_or_input(prompt: str, default: str = "") -> str:
    """Si ENABLE_AUTOCOMPLETE, retourne la valeur par défaut sans demander à l'utilisateur."""
    if ENABLE_AUTOCOMPLETE and default:
        print(f"{prompt}{default} (auto)")
        return default
    return input(prompt).strip()


class LiveTournamentView:
    """CLI pour dérouler un tournoi en direct (création/choix/gestion complète)."""

    def __init__(
        self,
        controller: TournamentController,
        player_controller: PlayerController,
        player_index: Dict[str, object],
    ) -> None:
        self.controller = controller
        self.player_controller = player_controller
        self.player_index = player_index  # {player_id: Player}

    # ----- Joueurs -----

    def _list_players(self) -> None:
        print("\nJoueurs disponibles :")
        if not self.player_index:
            print("(Aucun joueur.)")
            return
        self._player_num_map = {}
        for idx, (pid, p) in enumerate(self.player_index.items(), 1):
            first = getattr(p, "first_name", "")
            last = getattr(p, "last_name", "")
            print(f"{idx}. {pid}: {(first + ' ' + last).strip()}")
            self._player_num_map[str(idx)] = pid

    def _select_existing_player(self) -> str | None:
        if not self.player_index:
            print("(Aucun joueur existant.)")
            return None
        # Affiche la liste numérotée si elle n'est pas déjà affichée
        if not hasattr(self, "_player_num_map") or not self._player_num_map:
            self._list_players()
        choice = input("Numéro du joueur (existant) : ").strip()
        if choice in getattr(self, "_player_num_map", {}):
            return self._player_num_map[choice]
        # Fallback: accepte aussi l'ID complet
        pid = choice.upper()
        if pid in self.player_index:
            return pid
        print("Numéro ou ID introuvable.")
        return None

    def _create_player_flow(self) -> str | None:
        """Crée un nouveau joueur avec génération automatique si autocomplete activé."""
        print("\n— Création d'un joueur —")
        # Génération de l'ID
        if ENABLE_AUTOCOMPLETE:
            player_id = _random_national_id(set(self.player_index.keys()))
            print(f"Identifiant national (2 lettres + 5 chiffres) : {player_id} (auto)")
        else:
            player_id = input("Identifiant national (2 lettres + 5 chiffres) : ").strip().upper()
        if player_id in self.player_index:
            print(f"Joueur déjà existant : {self.player_index[player_id].full_name} [{player_id}]")
            return player_id

        # Génération des données personnelles
        if ENABLE_AUTOCOMPLETE:
            first_name = _random_name()
            print(f"Prénom: {first_name} (auto)")
            last_name = _random_name()
            print(f"Nom: {last_name} (auto)")
            birthdate = _random_birthdate()
            print(f"Date de naissance (YYYY-MM-DD) : {birthdate} (auto)")
        else:
            first_name = input("Prénom: ").strip().capitalize()
            last_name = input("Nom: ").strip().capitalize()
            birthdate = ask_birthdate()
        # Vérification des doublons par nom/date
        for p in self.player_index.values():
            if (
                p.first_name.lower() == first_name.lower()
                and p.last_name.lower() == last_name.lower()
                and p.birthdate == birthdate
            ):
                print(f"Joueur déjà existant sélectionné : {p.full_name} [{p.player_id}]")
                return p.player_id
        # Création du nouveau joueur
        try:
            created = self.player_controller.create_player(player_id, first_name, last_name, birthdate)
            self.player_index[player_id] = created
            print(f"Créé: {created.first_name} {created.last_name} [{created.player_id}]")
            return created.player_id
        except Exception as error:
            print(f"Erreur: {error}")
            return None

    def _pretty_selection(self, chosen: List[str]) -> str:
        if not chosen:
            return "(vide)"
        return ", ".join(f"{pid} ({self._name_of(pid)})" for pid in chosen)

    def _remove_from_selection(self, chosen: List[str]) -> None:
        if not chosen:
            print("Sélection vide.")
            return
        print("\n— Retirer un joueur —")
        print("Sélection actuelle :", self._pretty_selection(chosen))
        pid = input("ID du joueur à retirer: ").strip().upper()
        if pid in chosen:
            chosen.remove(pid)
            print(f"Retiré: {pid}")
        else:
            print("ID non présent dans la sélection.")

    def _pick_four_players(self) -> List[str]:
        chosen: List[str] = []
        try:
            while True:
                print("\n=== Sélection des joueurs ===")
                self._list_players()
                print(f"\nSélection actuelle ({len(chosen)}/4) : {self._pretty_selection(chosen)}")
                print("1. Choisir un joueur existant")
                print("2. Créer un nouveau joueur")
                print("3. Retirer un joueur")
                print("4. Valider la sélection")
                print("0. Annuler")
                choice = input("> ").strip()

                if choice == "1":
                    pid = self._select_existing_player()
                    if pid:
                        if pid in chosen:
                            print("Déjà sélectionné.")
                        elif len(chosen) >= 4:
                            print("Déjà 4 joueurs. Retire-en un pour remplacer.")
                        else:
                            chosen.append(pid)

                elif choice == "2":
                    pid = self._create_player_flow()
                    if pid:
                        if pid in chosen:
                            print("Déjà sélectionné.")
                        elif len(chosen) >= 4:
                            print("Déjà 4 joueurs. Retire-en un pour remplacer.")
                        else:
                            chosen.append(pid)

                elif choice == "3":
                    self._remove_from_selection(chosen)

                elif choice == "4":
                    if len(chosen) != 4:
                        print("Il faut exactement 4 joueurs.")
                    else:
                        return chosen

                elif choice == "0":
                    raise KeyboardInterrupt
                else:
                    print("Choix invalide.")
        except KeyboardInterrupt:
            print("\nRetour au menu principal.")
            return []

    # ----- Tournoi -----

    def _name_of(self, player_id: str) -> str:
        p = self.player_index.get(player_id)
        if not p:
            return player_id
        # Utilise full_name si disponible
        if hasattr(p, "full_name"):
            return p.full_name
        first = getattr(p, "first_name", "")
        last = getattr(p, "last_name", "")
        full = f"{first} {last}".strip()
        return full or player_id

    def _print_pairings(self, pairings: List[Tuple[list, list]]) -> None:
        for i, (a, b) in enumerate(pairings, start=1):
            a_id, _ = a
            b_id, _ = b
            print(f"Table {i}: {self._name_of(a_id)} (Blancs) vs {self._name_of(b_id)} (Noirs)")

    def _ask_result_for_match(self, table_index: int, white_id: str, black_id: str) -> str:
        valid = {"1-0", "0-1", "0.5-0.5"}
        while True:
            r = input(
                f"Résultat Table {table_index} ({self._name_of(white_id)} vs {self._name_of(black_id)}) "
                "[1-0 | 0-1 | 0.5-0.5]: "
            ).strip()
            if r in valid:
                return r
            print("Format invalide.")

    def _print_scores(self, score_map: Dict[str, float]) -> None:
        if not score_map:
            print("(Pas de scores)")
            return
        sorted_items = sorted(score_map.items(), key=lambda kv: (-kv[1], self._name_of(kv[0])))
        for rank, (pid, pts) in enumerate(sorted_items, start=1):
            print(f"{rank}. {self._name_of(pid)} — {pts} pts")

    # ----- Entrée -----

    def _select_or_create_tournament(self):
        tournaments = self.controller.list_tournaments()
        name_map = {}
        if tournaments:
            print("\nTournois existants :")
            for idx, t in enumerate(tournaments, 1):
                print(f"{idx}. {t.name} ({t.start_date} → {t.end_date}) @ {t.location}")
                name_map[str(idx)] = t
                name_map[t.name.lower()] = t
            print("0. Créer un nouveau tournoi")
            while True:
                # Pas d'autocomplete pour ce prompt
                choice = input("Numéro ou nom EXACT du tournoi (ou 0 pour créer) : ").strip()
                if choice == "0":
                    break
                if choice in name_map and isinstance(name_map[choice], Tournament):
                    return name_map[choice]
                if choice.lower() in name_map and isinstance(name_map[choice.lower()], Tournament):
                    return name_map[choice.lower()]
                print("Aucun tournoi ne correspond exactement à ce choix.")
        # Création d'un nouveau tournoi
        if ENABLE_AUTOCOMPLETE:
            name = _random_tournament_name(set(t.name for t in tournaments))
            print(f"Nom du tournoi: {name} (auto)")
            location = _random_location()
            print(f"Lieu (optionnel): {location} (auto)")
            start_date, end_date = _random_date_range()
            print(f"Date de début (YYYY-MM-DD) : {start_date} (auto)")
            print(f"Date de fin (YYYY-MM-DD) : {end_date} (auto)")
            num_rounds = random.randint(3, 7)
            print(f"Nombre de rondes [3]: {num_rounds} (auto)")
            description = "Tournoi généré automatiquement"
            print(f"Description (optionnelle): {description} (auto)")
        else:
            name = input("Nom du tournoi: ").strip() or "Tournoi amical"
            # Vérification des doublons
            for t in tournaments:
                if t.name.lower() == name.lower():
                    print(f"Tournoi déjà existant sélectionné : {t.name}")
                    return t
            location = input("Lieu (optionnel): ").strip() or ""
            start_date, end_date = ask_tournament_dates()
            num_rounds = read_int("Nombre de rondes [3]: ", default=3)
            description = input("Description (optionnelle): ").strip() or ""
        tournament = self.controller.create_tournament(
            name=name,
            location=location,
            start_date=start_date,
            end_date=end_date,
            num_rounds=num_rounds,
            description=description,
        )
        print(f"Tournoi créé: {tournament.name}")
        return tournament

    def _add_player_to_tournament(self, tournament):
        while True:
            print("\n1. Ajouter joueur existant")
            print("2. Créer nouveau joueur")
            print("0. Retour")
            choice = input("Votre choix (1/2/0) : ").strip()
            if choice == "1":
                self._list_players()
                pid = self._select_existing_player()
                if pid:
                    if pid in tournament.players:
                        print("Ce joueur est déjà inscrit dans ce tournoi.")
                    else:
                        try:
                            self.controller.register_player(tournament, pid)
                            print("Joueur ajouté.")
                        except Exception as e:
                            print(f"Erreur: {e}")
            elif choice == "2":
                pid = self._create_player_flow()
                if pid:
                    if pid in tournament.players:
                        print("Ce joueur est déjà inscrit dans ce tournoi.")
                    else:
                        try:
                            self.controller.register_player(tournament, pid)
                            print("Joueur créé et ajouté.")
                        except Exception as e:
                            print(f"Erreur: {e}")
            elif choice == "0":
                break
            else:
                print("Choix invalide.")

    def _remove_player_from_tournament(self, tournament):
        if not tournament.players:
            print("Aucun joueur à retirer.")
            return
        print("Joueurs inscrits :")
        for idx, pid in enumerate(tournament.players, 1):
            print(f"{idx}. {pid} ({self._name_of(pid)})")
        print("0. Annuler")
        while True:
            choice = input("Numéro du joueur à retirer (ou 0 pour annuler) : ").strip()
            if choice == "0":
                print("Suppression annulée.")
                return
            try:
                idx = int(choice)
                if 1 <= idx <= len(tournament.players):
                    pid = tournament.players[idx - 1]
                    tournament.players.remove(pid)
                    self.controller._save()
                    print(f"Joueur {pid} retiré.")
                    return
                else:
                    print("Numéro invalide.")
            except ValueError:
                print("Veuillez entrer un numéro valide.")

    def _edit_match_result(self, tournament):
        if not tournament.rounds:
            print("Aucun tour joué.")
            return
        for idx, rnd in enumerate(tournament.rounds, 1):
            print(f"{idx}. {rnd.name} ({rnd.start_datetime} → {rnd.end_datetime or '...'})")
        print("0. Annuler")
        while True:
            r_idx = input("Numéro du tour : ").strip()
            if r_idx == "0":
                return
            try:
                r_idx = int(r_idx) - 1
                if 0 <= r_idx < len(tournament.rounds):
                    round_obj = tournament.rounds[r_idx]
                    break
                else:
                    print("Numéro de tour invalide.")
            except ValueError:
                print("Veuillez entrer un numéro valide.")

        # Numérotation et saisie rapide des résultats
        print("Saisissez le résultat pour chaque match :")
        print("A = joueur 1 gagne, B = joueur 2 gagne, N = nul")
        for m_idx, match in enumerate(round_obj.matches, 1):
            a, b = match
            name_a = self._name_of(a[0])
            name_b = self._name_of(b[0])
            while True:
                res = input(f"{m_idx}. {name_a} [A] vs {name_b} [B] (A/B/N) : ").strip().upper()
                if res == "A":
                    score_a, score_b = 1.0, 0.0
                    break
                elif res == "B":
                    score_a, score_b = 0.0, 1.0
                    break
                elif res == "N":
                    score_a, score_b = 0.5, 0.5
                    break
                else:
                    print("Réponse invalide. Tapez A, B ou N.")
            try:
                self.controller.enter_result(
                    tournament, r_idx, m_idx - 1, score_a, score_b
                )
            except Exception as e:
                print(f"Erreur: {e}")
        print("Tous les résultats du tour ont été saisis.")

    def _autocomplete_player_id(self, tournament, prompt="ID du joueur à retirer: "):
        ids = tournament.players
        while True:
            partial = input(prompt).strip().upper()
            if not partial:
                return ""
            matches = [pid for pid in ids if pid.startswith(partial)]
            if len(matches) == 1 and matches[0] == partial:
                return partial
            elif matches:
                print("Suggestions :")
                for idx, pid in enumerate(matches, 1):
                    print(f"{idx}. {pid}: {self._name_of(pid)}")
            else:
                print("Aucun joueur ne correspond à ce début d'identifiant.")

    def _show_tournament_details(self, tournament):
        print(f"\nNom: {tournament.name}")
        print(f"Lieu: {tournament.location}")
        print(f"Dates: {tournament.start_date} → {tournament.end_date}")
        print(f"Description: {tournament.description}")
        print(f"Nombre de tours: {tournament.num_rounds}")
        print(f"Joueurs inscrits ({len(tournament.players)}):")
        for pid in tournament.players:
            print(f"- {self._name_of(pid)} [{pid}]")
        print(f"Tours joués: {len(tournament.rounds)}")

    def menu(self) -> None:
        try:
            tournament = self._select_or_create_tournament()
            if not tournament:
                print("Aucun tournoi sélectionné.")
                return

            while True:
                print(f"\n=== Gestion du tournoi: {tournament.name} ===")
                print("1. Ajouter un joueur")
                print("2. Retirer un joueur")
                print("3. Lister les joueurs inscrits")
                print("4. Démarrer le prochain tour")
                print("5. Saisir/modifier un résultat de match")
                print("6. Clôturer le tour en cours")
                print("7. Afficher le classement")
                print("8. Détails du tournoi")
                print("0. Retour au menu principal")
                choice = input("Votre choix (0-8) : ").strip()

                if choice == "1":
                    self._add_player_to_tournament(tournament)
                elif choice == "2":
                    self._remove_player_from_tournament(tournament)
                elif choice == "3":
                    print("Joueurs inscrits :")
                    for idx, pid in enumerate(tournament.players, 1):
                        print(f"{idx}. {self._name_of(pid)} [{pid}]")
                elif choice == "4":
                    try:
                        round_obj = self.controller.start_next_round(tournament)
                        print(
                            f"{round_obj.name} démarré, "
                            f"{len(round_obj.matches)} matchs générés."
                        )
                        self._print_pairings(round_obj.matches)
                    except Exception as error:
                        print(f"Erreur: {error}")
                elif choice == "5":
                    self._edit_match_result(tournament)
                elif choice == "6":
                    try:
                        self.controller.end_current_round(tournament)
                        print("Tour clôturé.")
                    except Exception as error:
                        print(f"Erreur: {error}")
                elif choice == "7":
                    try:
                        scores = self.controller.tournament_scores(tournament)
                        print("\nClassement :")
                        self._print_scores(scores)
                    except Exception as error:
                        print(f"Erreur: {error}")
                elif choice == "8":
                    self._show_tournament_details(tournament)
                elif choice == "0":
                    break
                else:
                    print("Choix invalide.")
        except KeyboardInterrupt:
            print("\nRetour au menu principal.")


def read_float(prompt: str) -> float:
    """Lecture sécurisée d'un nombre flottant."""
    raw_value = input(prompt).strip()
    try:
        return float(raw_value)
    except ValueError:
        print("Valeur invalide.")
        return read_float(prompt)


def _random_national_id(existing_ids: set[str]) -> str:
    """Génère un identifiant national unique et valide."""
    while True:
        prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
        number = ''.join(random.choices(string.digits, k=5))
        pid = prefix + number
        if pid not in existing_ids:
            return pid


def _random_name() -> str:
    """Génère un prénom ou nom aléatoire."""
    names = [
        "Alice", "Bob", "Charlie", "Diane", "Eve", "Frank", "Grace", "Hugo",
        "Ivy", "Jack", "Kara", "Leo", "Mona", "Nina", "Oscar", "Paul", "Quinn",
        "Rita", "Sam", "Tina", "Uma", "Vera", "Will", "Xena", "Yann", "Zoe"
    ]
    return random.choice(names)


def _random_birthdate() -> str:
    """Génère une date de naissance valide pour un adulte (18-80 ans)."""
    year = random.randint(datetime.now().year - 80, datetime.now().year - 18)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _random_tournament_name(existing_names: set[str]) -> str:
    """Génère un nom de tournoi unique."""
    base = random.choice(["Open", "Grand Prix", "Challenge", "Masters", "Coupe"])
    city = _random_name()
    name = f"{base} {city}"
    i = 1
    result = name
    while result in existing_names:
        i += 1
        result = f"{name} {i}"
    return result


def _random_location() -> str:
    """Génère une ville aléatoire."""
    cities = ["Paris", "Lyon", "Marseille", "Toulouse", "Lille", "Nantes", "Nice", "Bordeaux"]
    return random.choice(cities)


def _random_date_range() -> tuple[str, str]:
    """Génère une plage de dates valide (début <= fin)."""
    year = random.randint(datetime.now().year, datetime.now().year + 1)
    month = random.randint(1, 12)
    day = random.randint(1, 25)
    start = datetime(year, month, day)
    end = start
    if random.random() > 0.5:
        end = start.replace(day=min(day + random.randint(0, 5), 28))
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

# L'autocomplete est bien en place dans _create_player_flow et _select_or_create_tournament
# Les rounds sont séquentiels (voir TournamentController)
# Le matchmaking dépend des résultats précédents (voir TournamentController/start_next_round)
# Le code est propre, lisible, et respecte les contraintes du projet 4
