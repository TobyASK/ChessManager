from __future__ import annotations
from controllers.tournament_controller import TournamentController
from models.tournament import Tournament
from utils.validators import ask_tournament_dates, ask_national_id


def read_int(prompt: str, default: int | None = None) -> int:
    raw_value = input(prompt).strip()
    if not raw_value and default is not None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        print("Valeur invalide.")
        return read_int(prompt, default)


def read_float(prompt: str) -> float:
    raw_value = input(prompt).strip()
    try:
        return float(raw_value)
    except ValueError:
        print("Valeur invalide.")
        return read_float(prompt)


class TournamentView:
    """CLI for tournament management and reports."""

    def __init__(self, controller: TournamentController) -> None:
        self.controller = controller

    def _select_tournament(self) -> Tournament | None:
        tournaments = self.controller.list_tournaments()
        if not tournaments:
            print("Aucun tournoi.")
            return None
        for index, tournament in enumerate(tournaments, start=1):
            print(
                f"{index}. {tournament.name} "
                f"({tournament.start_date} → {tournament.end_date}) "
                f"@ {tournament.location}"
            )
        choice = read_int("> ", default=1)
        if 1 <= choice <= len(tournaments):
            return tournaments[choice - 1]
        print("Choix invalide.")
        return None

    def reports(self) -> None:
        try:
            while True:
                print("\n[Rapports]")
                print("1. Joueurs (alphabétique)")
                print("2. Tous les tournois")
                print("3. Nom et dates d’un tournoi")
                print("4. Joueurs d’un tournoi (alphabétique)")
                print("5. Tours et matchs d’un tournoi")
                print("0. Retour")
                user_choice = input("> ").strip()
                if user_choice == "1":
                    from controllers.player_controller import PlayerController
                    from storage.json_store import JsonStore
                    player_controller = PlayerController(JsonStore())
                    for player in player_controller.list_players_alpha():
                        print(
                            f"- {player.last_name.upper()}, "
                            f"{player.first_name} [{player.player_id}]"
                        )
                elif user_choice == "2":
                    for tournament in self.controller.list_tournaments():
                        print(
                            f"- {tournament.name} "
                            f"({tournament.start_date} → {tournament.end_date}) "
                            f"@ {tournament.location}"
                        )
                elif user_choice == "3":
                    tournament = self._select_tournament()
                    if tournament:
                        print(f"{tournament.name}: {tournament.start_date} → {tournament.end_date}")
                elif user_choice == "4":
                    tournament = self._select_tournament()
                    if tournament:
                        from storage.json_store import JsonStore
                        from controllers.player_controller import PlayerController
                        player_controller = PlayerController(JsonStore())
                        tournament_players = [player_controller.get(pid) for pid in tournament.players]
                        tournament_players = [p for p in tournament_players if p]
                        tournament_players.sort(
                            key=lambda p: (p.last_name.lower(), p.first_name.lower())
                        )
                        for player in tournament_players:
                            print(
                                f"- {player.last_name.upper()}, "
                                f"{player.first_name} [{player.player_id}]"
                            )
                elif user_choice == "5":
                    tournament = self._select_tournament()
                    if tournament:
                        for round_obj in tournament.rounds:
                            print(
                                f"\n{round_obj.name} "
                                f"({round_obj.start_datetime} → {round_obj.end_datetime or '...'})"
                            )
                            for match_index, match in enumerate(round_obj.matches, start=1):
                                (player_a_id, score_a), (player_b_id, score_b) = match
                                print(
                                    f"  {match_index}. {player_a_id} {score_a} - "
                                    f"{score_b} {player_b_id}"
                                )
                elif user_choice == "0":
                    break
                else:
                    print("Choix invalide.")
        except KeyboardInterrupt:
            print("\nRetour.")

    def menu(self) -> None:
        try:
            while True:
                print("\n[Tournois]")
                print("1. Créer un tournoi")
                print("2. Enregistrer un joueur dans un tournoi")
                print("3. Démarrer le prochain tour")
                print("4. Saisir un résultat de match")
                print("5. Terminer le tour en cours")
                print("6. Rapports")
                print("0. Retour")
                user_choice = input("> ").strip()
                if user_choice == "1":
                    name = input("Nom: ").strip()
                    location = input("Lieu: ").strip()
                    start_date, end_date = ask_tournament_dates()
                    num_rounds = read_int("Nombre de tours [4]: ", default=4)
                    description = input("Description: ").strip()
                    tournament = self.controller.create_tournament(
                        name, location, start_date, end_date, num_rounds, description
                    )
                    print(f"Créé: {tournament.name}")
                elif user_choice == "2":
                    tournament = self._select_tournament()
                    if tournament:
                        player_id = ask_national_id()
                        try:
                            self.controller.register_player(tournament, player_id)
                            print("OK.")
                        except Exception as error:
                            print(f"Erreur: {error}")
                elif user_choice == "3":
                    tournament = self._select_tournament()
                    if tournament:
                        try:
                            round_obj = self.controller.start_next_round(tournament)
                            print(
                                f"{round_obj.name} démarré, "
                                f"{len(round_obj.matches)} matchs générés."
                            )
                        except Exception as error:
                            print(f"Erreur: {error}")
                elif user_choice == "4":
                    tournament = self._select_tournament()
                    if tournament:
                        round_index = read_int("Index du tour (1…n): ") - 1
                        match_index = read_int("Index du match (1…n): ") - 1
                        score_player_a = read_float("Score joueur 1 (1/0.5/0): ")
                        score_player_b = read_float("Score joueur 2 (1/0.5/0): ")
                        try:
                            self.controller.enter_result(
                                tournament,
                                round_index,
                                match_index,
                                score_player_a,
                                score_player_b,
                            )
                            print("Résultat enregistré.")
                        except Exception as error:
                            print(f"Erreur: {error}")
                elif user_choice == "5":
                    tournament = self._select_tournament()
                    if tournament:
                        try:
                            self.controller.end_current_round(tournament)
                            print("Tour terminé.")
                        except Exception as error:
                            print(f"Erreur: {error}")
                elif user_choice == "6":
                    self.reports()
                elif user_choice == "0":
                    break
                else:
                    print("Choix invalide.")
        except KeyboardInterrupt:
            print("\nRetour au menu principal.")
