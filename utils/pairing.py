from __future__ import annotations
import random
from typing import List, Tuple, Dict

Match = Tuple[list, list]  # ([player_id, score], [player_id, score])


def first_round(player_ids: List[str]) -> List[Match]:
    shuffled_ids = player_ids[:]
    random.shuffle(shuffled_ids)
    matches: List[Match] = []
    for index in range(0, len(shuffled_ids), 2):
        if index + 1 < len(shuffled_ids):
            matches.append([[shuffled_ids[index], 0.0], [shuffled_ids[index + 1], 0.0]])
    return matches


def compute_scores(round_list: list) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for round_obj in round_list:
        for (player_a, score_a), (player_b, score_b) in round_obj.matches:
            scores[player_a] = scores.get(player_a, 0.0) + float(score_a)
            scores[player_b] = scores.get(player_b, 0.0) + float(score_b)
    return scores


def next_round(player_ids: List[str], round_list: list) -> List[Match]:
    scores_by_player = compute_scores(round_list)
    # Trie les joueurs par score décroissant, puis par nom pour stabilité
    ordered_players = sorted(
        player_ids,
        key=lambda pid: (-scores_by_player.get(pid, 0.0), pid)
    )
    matches: List[Match] = []
    for i in range(0, len(ordered_players), 2):
        if i + 1 < len(ordered_players):
            matches.append([[ordered_players[i], 0.0], [ordered_players[i + 1], 0.0]])
    return matches
