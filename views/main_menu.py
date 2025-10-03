from __future__ import annotations
from storage.json_store import JsonStore
from controllers.player_controller import PlayerController
from controllers.tournament_controller import TournamentController
from views.player_view import PlayerView
from views.tournament_view import TournamentView


class MainMenu:
    """Main menu for the Centre Échecs CLI application."""

    def __init__(self) -> None:
        self.store = JsonStore()
        self.player_controller = PlayerController(self.store)
        self.player_index = {player.player_id: player for player in self.player_controller.players}
        self.tournament_controller = TournamentController(self.store, self.player_index)

    def run(self) -> None:
        try:
            while True:
                print("\n=== Centre Échecs ===")
                print("1. Joueurs")
                print("2. Tournois")
                print("0. Quitter")
                user_choice = input("> ").strip()
                if user_choice == "1":
                    PlayerView(self.player_controller).menu()
                    self.player_index = {player.player_id: player for player in self.player_controller.players}
                    self.tournament_controller.player_index = self.player_index
                elif user_choice == "2":
                    TournamentView(self.tournament_controller).menu()
                elif user_choice == "0":
                    break
                else:
                    print("Choix invalide.")
        except KeyboardInterrupt:
            print("\nAu revoir.")
