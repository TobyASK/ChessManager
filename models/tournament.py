from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

Match = Tuple[List[object], List[object]]  # ([player_id, score], [player_id, score])


@dataclass
class Round:
    name: str
    start_datetime: str
    end_datetime: Optional[str] = None
    matches: List[Match] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start_datetime": self.start_datetime,
            "end_datetime": self.end_datetime,
            "matches": self.matches,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Round":
        return Round(
            name=data["name"],
            start_datetime=data["start_datetime"],
            end_datetime=data.get("end_datetime"),
            matches=[tuple(match) for match in data.get("matches", [])],
        )


@dataclass
class Tournament:
    name: str
    location: str
    start_date: str
    end_date: str
    num_rounds: int = 4
    current_round_index: int = 0
    rounds: List[Round] = field(default_factory=list)
    players: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "num_rounds": self.num_rounds,
            "current_round_index": self.current_round_index,
            "rounds": [round_obj.to_dict() for round_obj in self.rounds],
            "players": self.players,
            "description": self.description,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Tournament":
        return Tournament(
            name=data["name"],
            location=data["location"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            num_rounds=data.get("num_rounds", 4),
            current_round_index=data.get("current_round_index", 0),
            rounds=[Round.from_dict(round_dict) for round_dict in data.get("rounds", [])],
            players=list(data.get("players", [])),
            description=data.get("description", ""),
        )

    def start_new_round(self) -> Round:
        if self.current_round_index >= self.num_rounds:
            raise ValueError("Le tournoi est déjà terminé.")
        # Vérifie qu'il n'y a pas de round en cours (non terminé)
        if self.rounds and self.rounds[-1].end_datetime is None:
            raise ValueError("Le tour précédent n'est pas terminé.")
        round_name = f"Round {self.current_round_index + 1}"
        round_obj = Round(
            name=round_name,
            start_datetime=datetime.now().isoformat(timespec="seconds"),
        )
        self.rounds.append(round_obj)
        return round_obj

    def end_current_round(self) -> None:
        if self.current_round_index >= len(self.rounds):
            raise ValueError("Aucun tour en cours.")
        self.rounds[self.current_round_index].end_datetime = datetime.now().isoformat(timespec="seconds")
        self.current_round_index += 1
