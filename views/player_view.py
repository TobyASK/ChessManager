from __future__ import annotations
from datetime import datetime
from controllers.player_controller import PlayerController
from utils.validators import ask_national_id, ask_birthdate


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
                print("3. Modifier un joueur")
                print("0. Retour")
                user_choice = input("> ").strip()
                if user_choice == "1":
                    for player in self.controller.list_players_alpha():
                        name = getattr(
                            player, "full_name", f"{player.first_name} {player.last_name}"
                        )
                        print(
                            f"- {name} "
                            f"[{player.player_id}] ({player.birthdate})"
                        )
                elif user_choice == "2":
                    player_id = ask_national_id()
                    first_name = input("Prénom: ").strip().capitalize()
                    last_name = input("Nom: ").strip().capitalize()
                    birthdate = ask_birthdate()
                    try:
                        created = self.controller.create_player(
                            player_id, first_name, last_name, birthdate
                        )
                        print(f"Créé: {created.full_name} [{created.player_id}]")
                    except Exception as error:
                        print(f"Erreur: {error}")
                elif user_choice == "3":
                    player_id = ask_national_id()
                    player = self.controller.get(player_id)
                    if not player:
                        print("Joueur introuvable.")
                        continue
                    print(f"Modification de {player.full_name} [{player.player_id}]")
                    first_name = input(f"Prénom [{player.first_name}]: ").strip().capitalize() or player.first_name
                    last_name = input(f"Nom [{player.last_name}]: ").strip().capitalize() or player.last_name
                    birthdate = input(f"Date de naissance [{player.birthdate}]: ").strip() or player.birthdate
                    self.controller.update_player(
                        player_id,
                        first_name=first_name,
                        last_name=last_name,
                        birthdate=birthdate,
                    )
                    print("Joueur mis à jour.")
                elif user_choice == "0":
                    break
                else:
                    print("Choix invalide.")
        except KeyboardInterrupt:
            print("\nRetour au menu principal.")
