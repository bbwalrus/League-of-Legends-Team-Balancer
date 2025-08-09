from itertools import combinations

def balance_teams_by_role(players):
    n = len(players)
    if n % 2 != 0:
        raise ValueError("Number of players must be even")

    roles = list(players[0]["scores_by_role"].keys())
    half = n // 2
    best_score = float('inf')
    best_team_a = None
    penalty_weight = 20  # tune for discouraging unbalanced advantages

    def sum_scores(team):
        sums = {role: 0 for role in roles}
        for p in team:
            for r in roles:
                score = p["scores_by_role"].get(r) or 0
                sums[r] += score
        return sums

    for team_a_indices in combinations(range(n), half):
        team_a = [players[i] for i in team_a_indices]
        team_b = [players[i] for i in range(n) if i not in team_a_indices]

        sums_a = sum_scores(team_a)
        sums_b = sum_scores(team_b)

        role_diffs = {r: sums_a[r] - sums_b[r] for r in roles}
        abs_diff_sum = sum(abs(v) for v in role_diffs.values())

        # Count how many roles Team A and Team B "win"
        a_wins = sum(1 for v in role_diffs.values() if v > 0)
        b_wins = sum(1 for v in role_diffs.values() if v < 0)

        # Penalize imbalance in advantage counts
        advantage_imbalance = abs(a_wins - b_wins) * penalty_weight

        total_score = abs_diff_sum + advantage_imbalance

        if total_score < best_score:
            best_score = total_score
            best_team_a = team_a
            best_team_b = team_b
            if best_score == 0:
                break

    return (
        [p["player_id"] for p in best_team_a],
        [p["player_id"] for p in best_team_b]
    )

def balance_teams_by_role_average(players):
    """
    players: list of player dicts with 'scores_by_role' and 'player_id'
    
    Assign each player a role by their highest score (or any heuristic),
    then balance teams by minimizing difference in average scores of assigned roles.
    """
    roles = list(players[0]["scores_by_role"].keys())

    # Assign role to each player - pick role with highest score
    for p in players:
        best_role = max(roles, key=lambda r: p["scores_by_role"].get(r, 0))
        p["assigned_role"] = best_role
        p["assigned_score"] = p["scores_by_role"].get(best_role, 0)

    # Sort players by assigned_score descending
    sorted_players = sorted(players, key=lambda x: x["assigned_score"], reverse=True)

    team_a = []
    team_b = []
    sum_a = 0
    sum_b = 0

    # Greedy assign to balance total assigned_score
    for p in sorted_players:
        if sum_a <= sum_b:
            team_a.append(p)
            sum_a += p["assigned_score"]
        else:
            team_b.append(p)
            sum_b += p["assigned_score"]

    # Return player IDs with assigned roles for frontend
    return (
        [p["player_id"] for p in team_a],
        [p["player_id"] for p in team_b]
    )


def balance_teams_by_overall_average(players):
    # Compute average score per player
    for p in players:
        scores = list(p["scores_by_role"].values())
        p["average_score"] = sum(scores) / len(scores) if scores else 0

    # Sort players by average_score descending
    sorted_players = sorted(players, key=lambda x: x["average_score"], reverse=True)

    team_a = []
    team_b = []
    sum_a = 0
    sum_b = 0

    for p in sorted_players:
        if sum_a <= sum_b:
            team_a.append(p)
            sum_a += p["average_score"]
        else:
            team_b.append(p)
            sum_b += p["average_score"]

    return (
        [p["player_id"] for p in team_a],
        [p["player_id"] for p in team_b]
    )
