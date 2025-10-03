from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Player:
    """Player with a national chess identifier."""

    player_id: str  # Format AB12345
    first_name: str
    last_name: str
    birthdate: str  # YYYY-MM-DD

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def from_dict(data: Dict) -> "Player":
        return Player(
            player_id=data["player_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            birthdate=data["birthdate"],
        )
