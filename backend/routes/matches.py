from fastapi import APIRouter, Depends
from database import get_connection
from scraper import fetch_and_store_scores

router = APIRouter()

# updates match history for a player given their user, tag, and role as well as how many pages back to go history wise
@router.post("/matches/fetch")
def fetch_player_matches(summoner_name: str, tag: str, role: str, pages: int = 5):
    conn = get_connection()
    fetch_and_store_scores(conn, summoner_name, tag, role, pages)
    return {"message": f"Matches for {summoner_name}#{tag} ({role}) fetched and stored."}
