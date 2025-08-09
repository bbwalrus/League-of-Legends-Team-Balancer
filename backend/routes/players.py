from fastapi import APIRouter, Depends, HTTPException
from database import get_connection, get_player_id, get_player_aggregates
from scraper import fetch_and_store_scores
import concurrent.futures
from datetime import datetime, timedelta

router = APIRouter()

# endpoint where given a username and tag, returns their role scores
import concurrent.futures
from datetime import datetime, timedelta

@router.get("/players/{summoner_name}/{tag}")
def get_player_scores(summoner_name: str, tag: str):
    summoner_name = summoner_name.lower()
    tag = tag.lower()
    conn = get_connection()
    player_key = summoner_name + "-" + tag
    player_id = get_player_id(conn, player_key)

    roles = ['top', 'jungle', 'middle', 'bottom', 'utility']
    aggregates_list = get_player_aggregates(conn, player_id)
    aggregates_by_role = {agg['role']: agg for agg in aggregates_list}

    def fetch_role(role):
        agg = aggregates_by_role.get(role)
        now = datetime.now()
        # Check if aggregate exists and updated in last 24h
        if agg and agg.get('last_updated'):
            last_updated = agg['last_updated']
            if isinstance(last_updated, str):
                # parse string to datetime if necessary
                last_updated = datetime.fromisoformat(last_updated)
            if now - last_updated < timedelta(hours=24):
                return  # skip fetch, data is fresh
        # Determine depth
        depth = 5 if (not agg or agg['total_matches'] == 0) else 1
        fetch_and_store_scores(conn, summoner_name, tag, role, depth)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(fetch_role, roles)  # waits for all to complete

    # Refresh aggregates after fetching
    player_id = get_player_id(conn, player_key)
    updated_aggregates = get_player_aggregates(conn, player_id)
    return {"player_id": player_id, "aggregates": updated_aggregates}
