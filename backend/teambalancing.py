from itertools import combinations

def balance_teams_by_role(players):
    n = len(players)
    if n % 2 != 0:
        raise ValueError("Number of players must be even")

    roles = list(players[0]["scores_by_role"].keys())
    half = n // 2
    best_diff = float('inf')
    best_team_a = None

    # Generate all combinations of half the players for team_a
    # This is only feasible for small n (e.g., 10 players: C(10,5) = 252)
    for team_a_indices in combinations(range(n), half):
        team_a = [players[i] for i in team_a_indices]
        team_b = [players[i] for i in range(n) if i not in team_a_indices]

        # Sum scores by role for each team
        def sum_scores(team):
            sums = {role: 0 for role in roles}
            for p in team:
                for r in roles:
                    score = p["scores_by_role"].get(r)
                    if score is None:
                        score = 0
                    sums[r] += score
            return sums

        sums_a = sum_scores(team_a)
        sums_b = sum_scores(team_b)

        # Calculate total absolute difference across roles
        diff = sum(abs(sums_a[r] - sums_b[r]) for r in roles)

        if diff < best_diff:
            best_diff = diff
            best_team_a = team_a
            best_team_b = team_b
            if best_diff == 0:
                break  # perfect balance

    # Return player_id lists for each team
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
