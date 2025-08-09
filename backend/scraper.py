from bs4 import BeautifulSoup
import time
import random
import re
import requests
from database import get_connection, insert_or_update_player, get_player_puuid, insert_match, update_player_role_aggregate
from dotenv import load_dotenv
import os

load_dotenv()
BASE_URL = os.getenv("BASE_URL")

def get_scores(summoner_name: str, tag: str, lane: str, pages: int):
    user_id = f"{summoner_name}-{tag}"
    scores = []

    # check if we already have the user in the db
    with get_connection() as conn:
        puuid = get_player_puuid(conn, user_id)

        # if not add the user with their puuid
        if not puuid:
            print(f"PUUID not found for {user_id}, fetching from API...")
            puuid = get_puuid(summoner_name, tag)
            if puuid:
                insert_or_update_player(conn, user_id, puuid)
            else:
                print(f"Failed to fetch PUUID for {user_id}")
                return []

        for page in range(1, pages + 1):
            url = f"{BASE_URL}/v1/players/{puuid}/match-history?lane={lane}&page={page}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch page {page}")
                continue

            data = response.json()
            matches = data.get("matches", [])

            # break loop early if no matches
            if not matches:
                print(f"No matches found on page {page}, stopping requests.")
                break
            
            for match in matches:
                # find the player
                for participant in match["participants"]:
                    if participant["puuid"] == puuid:
                        # take important info
                        scores.append({
                            "gameId": match["gameId"],
                            "date": match["gameCreation"],
                            "score": participant.get("dpmScore"),
                            "championName": participant.get("championName"),
                            "win": participant.get("win")
                        })
                        break
            sleep_time = random.uniform(0, 3)
            print(f"Sleeping for {sleep_time:.2f} seconds before next request...")
            time.sleep(sleep_time)

    return scores

def get_puuid(username, tag):
    url = f"{BASE_URL}/{username}-{tag}"
    response = requests.get(url)
    html = response.text
    
    return extract_puuid_from_nextjs(html)

def extract_puuid_from_nextjs(html):
    soup = BeautifulSoup(html, "html.parser")
    puuid = None

    # Find all script tags
    for script in soup.find_all("script"):
        if script.string and "self.__next_f.push" in script.string:
            # Extract the JSON-like payload inside self.__next_f.push([...])
            # Pattern to extract the first argument array's second element (the string)
            match = re.search(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', script.string, re.DOTALL)
            if match:
                payload_str = match.group(1)

                # This string is heavily escaped, so unescape sequences like \n, \", etc.
                unescaped = bytes(payload_str, "utf-8").decode("unicode_escape")

                # Find puuid by regex in unescaped string
                puuid_match = re.search(r'"puuid":"([a-zA-Z0-9_-]{40,})"', unescaped)
                if puuid_match:
                    puuid = puuid_match.group(1)
                    return puuid
    return None

def fetch_and_store_scores(conn, summoner_name: str, tag: str, role: str, pages: int = 5):
    user_id = f"{summoner_name}-{tag}"

    # Step 1: Fetch scores
    scores = get_scores(summoner_name, tag, role, pages)

    # Step 2: Get player_id
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM players WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        if result is None:
            print(f"[WARN] Player not found in database: {user_id}")
            return
        player_id = result[0]

    # Step 3: Insert each match
    for match in scores:
        try:
            insert_match(
                conn=conn,
                player_id=player_id,
                role=role,
                game_id=match["gameId"],
                date=match["date"],
                score=match["score"],
                champion_name=match["championName"],
                win=match["win"]
            )
        except Exception as e:
            print(f"[ERROR] Failed to insert match {match['gameId']}: {e}")

    # Step 4: Update role aggregates
    update_player_role_aggregate(conn, player_id, role)

    print(f"[INFO] Stored {len(scores)} matches for {user_id} in role {role}")

if __name__ == "__main__":
    print(get_scores("duckkchild", "duckk", "top", 2))