from __future__ import annotations
import re
from typing import List, Optional
from storage.json_store import JsonStore
from models.player import Player

NATIONAL_ID_PATTERN = re.compile(r"^[A-Z]{2}\d{5}$")


class PlayerController:
    """Manage player data and persistence."""

    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.players: List[Player] = store.load_players()

    def _save(self) -> None:
        self.store.save_players(self.players)

    def list_players_alpha(self) -> List[Player]:
        return sorted(
            self.players,
            key=lambda player: (player.last_name.lower(), player.first_name.lower()),
        )

    def create_player(
        self,
        player_id: str,
        first_name: str,
        last_name: str,
        birthdate: str,
    ) -> Player:
        if not NATIONAL_ID_PATTERN.match(player_id):
            raise ValueError("Identifiant national invalide (format AB12345).")
        if any(player.player_id == player_id for player in self.players):
            raise ValueError("Un joueur avec cet identifiant existe déjà.")
        new_player = Player(
            player_id=player_id,
            first_name=first_name,
            last_name=last_name,
            birthdate=birthdate,
        )
        # Ajoute full_name si absent
        if not hasattr(new_player, "full_name"):
            new_player.full_name = f"{first_name} {last_name}".strip()
        self.players.append(new_player)
        self._save()
        return new_player

    def get(self, player_id: str) -> Optional[Player]:
        return next((player for player in self.players if player.player_id == player_id), None)

    def exists(self, player_id: str) -> bool:
        return any(player.player_id == player_id for player in self.players)

    def update_player(self, player_id: str, **kwargs) -> Optional[Player]:
        player = self.get(player_id)
        if not player:
            return None
        for key, value in kwargs.items():
            if hasattr(player, key):
                setattr(player, key, value)
        self._save()
        return player

    def print_all(self) -> None:
        for player in self.players:
            print(player)
