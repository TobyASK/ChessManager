from __future__ import annotations
import json
from typing import List, Any
from pathlib import Path

from models.player import Player
from models.tournament import Tournament


class JsonStore:
    """JSON-backed storage for players and tournaments."""

    def __init__(
        self,
        players_file: str = "data/players.json",
        tournaments_file: str = "data/tournaments.json",
    ) -> None:
        self.players_path = Path(players_file)
        self.tournaments_path = Path(tournaments_file)
        self.players_path.parent.mkdir(parents=True, exist_ok=True)
        self.tournaments_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.players_path.exists():
            self._write_json(self.players_path, [])
        if not self.tournaments_path.exists():
            self._write_json(self.tournaments_path, [])

    @staticmethod
    def _read_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

    def load_players(self) -> List[Player]:
        raw_players = self._read_json(self.players_path)
        return [Player.from_dict(player_dict) for player_dict in raw_players]

    def save_players(self, players: List[Player]) -> None:
        self._write_json(self.players_path, [player.to_dict() for player in players])

    def load_tournaments(self) -> List[Tournament]:
        raw_tournaments = self._read_json(self.tournaments_path)
        return [Tournament.from_dict(tournament_dict) for tournament_dict in raw_tournaments]

    def save_tournaments(self, tournaments: List[Tournament]) -> None:
        self._write_json(self.tournaments_path, [tournament.to_dict() for tournament in tournaments])
