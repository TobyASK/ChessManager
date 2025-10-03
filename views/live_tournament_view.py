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
    """CLI pour dérouler un tournoi en direct (création/choix des joueurs)."""

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

    def menu(self) -> None:
        try:
            print("\n=== Tournoi (en direct) ===")
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

            player_ids = self._pick_four_players()
            if len(player_ids) != 4:
                return

            for pid in player_ids:
                try:
                    self.controller.register_player(tournament, pid)
                except Exception as error:
                    print(f"Erreur inscription {pid}: {error}")

            print("Joueurs inscrits !")

            current_round = 1
            while current_round <= num_rounds:
                print(f"\n=== Ronde {current_round}/{num_rounds} ===")
                try:
                    round_obj = self.controller.start_next_round(tournament)
                except Exception as error:
                    print(f"Erreur au démarrage du tour: {error}")
                    break

                pairings = round_obj.matches
                if not pairings:
                    print("(Aucun appariement)")
                    break
                self._print_pairings(pairings)

                for m_index, match in enumerate(pairings, start=1):
                    white_id = match[0][0]
                    black_id = match[1][0]
                    res = self._ask_result_for_match(m_index, white_id, black_id)
                    if res == "1-0":
                        s_a, s_b = 1.0, 0.0
                    elif res == "0-1":
                        s_a, s_b = 0.0, 1.0
                    else:
                        s_a, s_b = 0.5, 0.5
                    try:
                        round_index = getattr(tournament, "current_round_index", current_round - 1)
                        self.controller.enter_result(
                            tournament=tournament,
                            round_index=round_index,
                            match_index=m_index - 1,
                            score_player_a=s_a,
                            score_player_b=s_b,
                        )
                    except Exception as error:
                        print(f"Erreur enregistrement résultat Table {m_index}: {error}")

                try:
                    self.controller.end_current_round(tournament)
                except Exception as error:
                    print(f"Erreur clôture du tour: {error}")
                    break

                try:
                    scores = self.controller.tournament_scores(tournament)
                    print("\nClassement provisoire :")
                    self._print_scores(scores)
                except Exception as error:
                    print(f"Erreur calcul des scores: {error}")

                current_round += 1

            try:
                scores = self.controller.tournament_scores(tournament)
                print("\n=== Classement final ===")
                self._print_scores(scores)
            except Exception as error:
                print(f"Erreur calcul des scores finaux: {error}")

            print("Tournoi terminé !")
        except KeyboardInterrupt:
            print("\nRetour au menu principal.")
