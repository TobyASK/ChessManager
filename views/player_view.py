from __future__ import annotations
from datetime import datetime
from controllers.player_controller import PlayerController


def read_date_or_empty(prompt: str) -> str:
    raw_value = input(prompt).strip()
    if not raw_value:
        return ""
    try:
        datetime.strptime(raw_value, "%Y-%m-%d")
        return raw_value
    except ValueError:
        print("Format invalide. Attendu: YYYY-MM-DD. Valeur ignorée.")
        return ""


class PlayerView:
    """CLI for player management."""

    def __init__(self, controller: PlayerController) -> None:
        self.controller = controller

    def menu(self) -> None:
        try:
            while True:
                print("\n[Joueurs]")
                print("1. Lister (alphabétique)")
                print("2. Créer un joueur")
                print("0. Retour")
                user_choice = input("> ").strip()
                if user_choice == "1":
                    for player in self.controller.list_players_alpha():
                        print(
                            f"- {player.full_name} "
                            f"[{player.player_id}] ({player.birthdate})"
                        )
                elif user_choice == "2":
                    player_id = input("Identifiant national (ex: AB12345): ").strip().upper()
                    first_name = input("Prénom: ").strip()
                    last_name = input("Nom: ").strip()
                    birthdate = read_date_or_empty(
                        "Date de naissance (YYYY-MM-DD) [optionnel]: "
                    )
                    try:
                        created = self.controller.create_player(
                            player_id, first_name, last_name, birthdate
                        )
                        print(f"Créé: {created.full_name} [{created.player_id}]")
                    except Exception as error:
                        print(f"Erreur: {error}")
                elif user_choice == "0":
                    break
                else:
                    print("Choix invalide.")
        except KeyboardInterrupt:
            print("\nRetour au menu principal.")
