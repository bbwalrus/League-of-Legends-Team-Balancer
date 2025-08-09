import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_connection():
    """
    Creates and returns a psycopg2 connection to the database
    using credentials from environment variables.
    """
    try:
        connection = psycopg2.connect(
            user=os.getenv("user"),
            password=os.getenv("password"),
            host=os.getenv("host"),
            port=os.getenv("port"),
            dbname=os.getenv("dbname")
        )
        print("Database connection established.")
        return connection
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        return None

def create_tables():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                puuid TEXT UNIQUE NOT NULL
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                player_id INTEGER NOT NULL REFERENCES players(id),
                role TEXT NOT NULL,
                game_id BIGINT NOT NULL,
                date BIGINT NOT NULL,
                score REAL NOT NULL,
                champion_name TEXT NOT NULL,
                win BOOLEAN NOT NULL,
                UNIQUE(player_id, role, game_id)
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS player_role_aggregates (
                id SERIAL PRIMARY KEY,
                player_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                avg_score FLOAT,
                total_matches INTEGER,
                last_updated TIMESTAMP,
                UNIQUE (player_id, role)
            );
        ''')
        conn.commit()

# get the player PUUID from user + tag
def get_player_puuid(conn, user_id: str) -> str | None:
    cursor = conn.cursor()
    cursor.execute("SELECT puuid FROM players WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# get the player DATABASE UNIQUE ID from user + tag
def get_player_id(conn, user_id: str) -> int | None:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM players WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def insert_or_update_player(conn, user_id: str, puuid: str) -> int:
    """
    Insert player if not exists, or update puuid if changed.
    Returns player.id
    """
    cursor = conn.cursor()
    
    # Use %s placeholders
    cursor.execute("SELECT id, puuid FROM players WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    
    if row:
        player_id, old_puuid = row
        if old_puuid != puuid:
            cursor.execute("UPDATE players SET puuid=%s WHERE id=%s", (puuid, player_id))
            conn.commit()
        return player_id
    else:
        cursor.execute("INSERT INTO players (user_id, puuid) VALUES (%s, %s) RETURNING id", (user_id, puuid))
        player_id = cursor.fetchone()[0]
        conn.commit()
        return player_id

def insert_match(conn, player_id: int, role: str, game_id: int, date: int, score: float, champion_name: str, win: bool):
    if score is None:
        return  # skip insert if score is null
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO matches (player_id, role, game_id, date, score, champion_name, win)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id, role, game_id) DO NOTHING
        """, (player_id, role, game_id, date, score, champion_name, win))
        conn.commit()

def update_player_role_aggregate(conn, player_id, role):
    cursor = conn.cursor()
    # Calculate average score and count matches for this player & role
    cursor.execute("""
        SELECT AVG(score), COUNT(*)
        FROM matches
        WHERE player_id = %s AND role = %s
    """, (player_id, role))
    
    avg_score, total_matches = cursor.fetchone()
    
    if avg_score is None:
        # No matches found, remove from aggregates if exists
        cursor.execute("""
            DELETE FROM player_role_aggregates WHERE player_id = %s AND role = %s
        """, (player_id, role))
    else:
        # Upsert aggregate record
        cursor.execute("""
            INSERT INTO player_role_aggregates (player_id, role, avg_score, total_matches, last_updated)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (player_id, role)
            DO UPDATE SET
                avg_score = EXCLUDED.avg_score,
                total_matches = EXCLUDED.total_matches,
                last_updated = EXCLUDED.last_updated
        """, (player_id, role, avg_score, total_matches))
    conn.commit()

def get_player_aggregates(conn, player_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT role, avg_score, total_matches, last_updated
            FROM player_role_aggregates
            WHERE player_id = %s
        """, (player_id,))
        results = cur.fetchall()
        return [
            {
                "role": row[0],
                "avg_score": row[1],
                "total_matches": row[2],
                "last_updated": row[3]
            } for row in results
        ]
