from fastapi import APIRouter, HTTPException
import traceback
from pydantic import BaseModel
from typing import List, Dict
from teambalancing import balance_teams_by_role, balance_teams_by_role_average, balance_teams_by_overall_average
from typing import Optional

router = APIRouter()

class Summoner(BaseModel):
    name: str
    tag: str
    scores_by_role: Dict[str, Optional[float]]

class TeamBalanceRequest(BaseModel):
    summoners: List[Summoner]
    balance_type: str 

@router.post("/teams/balance")
def balance_teams_api(request: TeamBalanceRequest):
    try:
        players = [
            {
                "player_id": f"{s.name}#{s.tag}",
                "scores_by_role": {
                    "top": s.scores_by_role.get("top") or 0,
                    "jungle": s.scores_by_role.get("jungle") or 0,
                    "mid": s.scores_by_role.get("middle") or 0,
                    "adc": s.scores_by_role.get("bottom") or 0,
                    "support": s.scores_by_role.get("utility") or 0,
                }
            }
            for s in request.summoners
        ]

        if request.balance_type == "role_average":
            # Call a function that balances teams by average scores (you'll implement this)
            team_a, team_b = balance_teams_by_role_average(players)
        elif request.balance_type == "role":
            # Call a function that balances teams by role scores
            team_a, team_b = balance_teams_by_role(players)
        else:
            # Call a function that balances teams by overall average
            team_a, team_b = balance_teams_by_overall_average(players)

        return {"team_a": team_a, "team_b": team_b}

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error balancing teams: {e}"
        )
