from __future__ import annotations
import random
from typing import List, Tuple, Dict, Set

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


def played_pairs(round_list: list) -> Set[frozenset]:
    seen_pairs: Set[frozenset] = set()
    for round_obj in round_list:
        for (player_a, _), (player_b, _) in round_obj.matches:
            seen_pairs.add(frozenset((player_a, player_b)))
    return seen_pairs


def next_round(player_ids: List[str], round_list: list) -> List[Match]:
    scores_by_player = compute_scores(round_list)
    groups_by_score: Dict[float, List[str]] = {}
    for player_id in player_ids:
        player_score = scores_by_player.get(player_id, 0.0)
        groups_by_score.setdefault(player_score, []).append(player_id)

    ordered_players: List[str] = []
    for score in sorted(groups_by_score.keys(), reverse=True):
        group = groups_by_score[score]
        random.shuffle(group)
        ordered_players.extend(group)

    previous_pairs = played_pairs(round_list)
    matches: List[Match] = []
    used_players = set()

    for i, player_a in enumerate(ordered_players):
        if player_a in used_players:
            continue
        found_partner = False
        for player_b in ordered_players[i + 1:]:
            if player_b in used_players:
                continue
            if frozenset((player_a, player_b)) not in previous_pairs:
                matches.append([[player_a, 0.0], [player_b, 0.0]])
                used_players.update({player_a, player_b})
                found_partner = True
                break
        if not found_partner:
            # Fallback: pair with next available, even if already played
            for player_b in ordered_players[i + 1:]:
                if player_b not in used_players:
                    matches.append([[player_a, 0.0], [player_b, 0.0]])
                    used_players.update({player_a, player_b})
                    break
    return matches
