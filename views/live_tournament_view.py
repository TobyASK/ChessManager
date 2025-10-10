from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime
import dateparser
from controllers.tournament_controller import TournamentController
from controllers.player_controller import PlayerController
from utils.validators import ask_national_id, ask_birthdate, ask_tournament_dates


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
        for pid, p in self.player_index.items():
            first = getattr(p, "first_name", "")
            last = getattr(p, "last_name", "")
            print(f"- {pid}: {(first + ' ' + last).strip()}")

    def _select_existing_player(self) -> str | None:
        if not self.player_index:
            print("(Aucun joueur existant.)")
            return None
        pid = input("ID du joueur (existant) : ").strip().upper()
        if pid not in self.player_index:
            print("ID introuvable.")
            return None
        return pid

    def _create_player_flow(self) -> str | None:
        print("\n— Création d’un joueur —")
        player_id = ask_national_id()
        first_name = input("Prénom: ").strip().capitalize()
        last_name = input("Nom: ").strip().capitalize()
        birthdate = ask_birthdate()
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
        """Permet de choisir un tournoi existant ou d'en créer un nouveau."""
        tournaments = self.controller.list_tournaments()
        print("\nTournois existants :")
        for idx, t in enumerate(tournaments, 1):
            print(f"{idx}. {t.name} ({t.start_date} → {t.end_date}) @ {t.location}")
        print("0. Créer un nouveau tournoi")
        choice = read_int("> ", default=0)
        if choice == 0:
            name = input("Nom du tournoi: ").strip() or "Tournoi amical"
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
        elif 1 <= choice <= len(tournaments):
            return tournaments[choice - 1]
        else:
            print("Choix invalide.")
            return None

    def _add_player_to_tournament(self, tournament):
        while True:
            print("\n1. Ajouter joueur existant\n2. Créer nouveau joueur\n0. Retour")
            choice = input("> ").strip()
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
        for pid in tournament.players:
            print(f"- {pid} ({self._name_of(pid)})")
        pid = input("ID du joueur à retirer: ").strip().upper()
        if pid in tournament.players:
            tournament.players.remove(pid)
            self.controller._save()
            print("Joueur retiré.")
        else:
            print("ID non trouvé.")

    def _edit_match_result(self, tournament):
        if not tournament.rounds:
            print("Aucun tour joué.")
            return
        for idx, rnd in enumerate(tournament.rounds, 1):
            print(f"{idx}. {rnd.name} ({rnd.start_datetime} → {rnd.end_datetime or '...'})")
        r_idx = read_int("Numéro du tour: ", default=1) - 1
        if not (0 <= r_idx < len(tournament.rounds)):
            print("Tour invalide.")
            return
        round_obj = tournament.rounds[r_idx]
        for m_idx, match in enumerate(round_obj.matches, 1):
            a, b = match
            print(f"{m_idx}. {self._name_of(a[0])} ({a[1]}) vs {self._name_of(b[0])} ({b[1]})")
        m_idx = read_int("Numéro du match: ", default=1) - 1
        if not (0 <= m_idx < len(round_obj.matches)):
            print("Match invalide.")
            return
        score_a = read_float("Score joueur 1 (1/0.5/0): ")
        score_b = read_float("Score joueur 2 (1/0.5/0): ")
        try:
            self.controller.enter_result(
                tournament, r_idx, m_idx, score_a, score_b
            )
            print("Résultat modifié.")
        except Exception as e:
            print(f"Erreur: {e}")

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
                choice = input("> ").strip()

                if choice == "1":
                    self._add_player_to_tournament(tournament)
                elif choice == "2":
                    # Affiche la liste des joueurs inscrits avant suppression
                    if not tournament.players:
                        print("Aucun joueur à retirer.")
                    else:
                        print("Joueurs inscrits dans ce tournoi :")
                        for pid in tournament.players:
                            print(f"- {pid}: {self._name_of(pid)}")
                        pid = input("ID du joueur à retirer: ").strip().upper()
                        if pid in tournament.players:
                            self.controller.remove_player(tournament, pid)
                            print("Joueur retiré.")
                        else:
                            print("ID non trouvé dans ce tournoi.")
                elif choice == "3":
                    print("Joueurs inscrits :")
                    for pid in tournament.players:
                        print(f"- {self._name_of(pid)} [{pid}]")
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
    raw_value = input(prompt).strip()
    try:
        return float(raw_value)
    except ValueError:
        print("Valeur invalide.")
        return read_float(prompt)
