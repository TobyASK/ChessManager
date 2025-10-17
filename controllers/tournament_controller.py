from __future__ import annotations
from typing import List, Dict
from storage.json_store import JsonStore
from models.tournament import Tournament, Round
from models.player import Player
from utils.pairing import first_round, next_round, compute_scores


class TournamentController:
    """Manage tournament lifecycle and reporting."""

    def __init__(self, store: JsonStore, player_index: Dict[str, Player]) -> None:
        self.store = store
        self.tournaments: List[Tournament] = store.load_tournaments()
        self.player_index = player_index

    def _save(self) -> None:
        self.store.save_tournaments(self.tournaments)

    def list_tournaments(self) -> List[Tournament]:
        return list(self.tournaments)

    def create_tournament(
        self,
        name: str,
        location: str,
        start_date: str,
        end_date: str,
        num_rounds: int = 4,
        description: str = "",
    ) -> Tournament:
        tournament = Tournament(
            name=name,
            location=location,
            start_date=start_date,
            end_date=end_date,
            num_rounds=num_rounds,
            description=description,
        )
        self.tournaments.append(tournament)
        self._save()
        return tournament

    def register_player(self, tournament: Tournament, player_id: str) -> None:
        if player_id not in self.player_index:
            raise ValueError("Joueur introuvable.")
        if player_id not in tournament.players:
            tournament.players.append(player_id)
            self._save()  # Sauvegarde automatique après ajout

    def start_next_round(self, tournament: Tournament) -> Round:
        # Les rounds sont séquentiels : on ne peut pas démarrer un nouveau round si le précédent n'est pas terminé
        if tournament.current_round_index >= tournament.num_rounds:
            raise ValueError("Tous les tours ont déjà été joués.")
        if tournament.rounds and tournament.rounds[-1].end_datetime is None:
            raise ValueError("Le tour précédent n'est pas terminé.")
        round_obj = tournament.start_new_round()
        # Le matchmaking dépend des résultats précédents (next_round trie selon les scores)
        if tournament.current_round_index == 0:
            round_obj.matches = first_round(tournament.players)
        else:
            round_obj.matches = next_round(tournament.players, tournament.rounds)
        self._save()
        return round_obj

    def enter_result(
        self,
        tournament: Tournament,
        round_index: int,
        match_index: int,
        score_player_a: float,
        score_player_b: float,
    ) -> None:
        round_obj = tournament.rounds[round_index]
        player_a_id, _ = round_obj.matches[match_index][0]
        player_b_id, _ = round_obj.matches[match_index][1]
        round_obj.matches[match_index] = [
            [player_a_id, float(score_player_a)],
            [player_b_id, float(score_player_b)],
        ]
        self._save()  # Sauvegarde automatique après saisie du résultat

    def end_current_round(self, tournament: Tournament) -> None:
        tournament.end_current_round()
        self._save()  # Sauvegarde automatique après clôture du round

    def tournament_scores(self, tournament: Tournament) -> Dict[str, float]:
        return compute_scores(tournament.rounds)

    def remove_player(self, tournament: Tournament, player_id: str) -> None:
        if player_id in tournament.players:
            tournament.players.remove(player_id)
            self._save()  # Sauvegarde automatique après suppression

    def reset_tournament(self, tournament: Tournament) -> None:
        tournament.current_round_index = 0
        tournament.rounds.clear()
        self._save()  # Sauvegarde automatique après reset

    def get_by_name(self, name: str):
        for t in self.tournaments:
            if t.name == name:
                return t
        return None
