import json
import os
import sqlite3
import time
from typing import Dict, List
from models import Tournament

# Legacy JSON path (still used for one-time migration if present)
DATA_FILE = "tournaments_data.json"

# SQLite database file
DB_PATH = "tournaments.db"

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kv_store (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            mtime REAL NOT NULL
        )
        """
    )
    return conn

def _read_kv(key: str) -> tuple[str | None, float | None]:
    try:
        with _get_connection() as conn:
            cur = conn.execute("SELECT value, mtime FROM kv_store WHERE key=?", (key,))
            row = cur.fetchone()
            if row:
                return row[0], float(row[1])
            return None, None
    except Exception:
        return None, None

def _write_kv(key: str, value: str) -> bool:
    try:
        now = time.time()
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO kv_store(key, value, mtime) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, mtime=excluded.mtime",
                (key, value, now),
            )
        return True
    except Exception as e:
        print(f"Error writing to DB: {e}")
        return False

def get_store_mtime() -> float:
    """Return last modification time for tournaments store (0.0 if none)."""
    _, mtime = _read_kv("tournaments")
    return float(mtime or 0.0)

def _migrate_json_to_db_if_needed():
    """On first run, migrate existing JSON data into SQLite if DB is empty."""
    existing_value, _ = _read_kv("tournaments")
    if existing_value is not None:
        return
    if not os.path.exists(DATA_FILE):
        # No legacy file, initialize empty store
        _write_kv("tournaments", json.dumps({}, ensure_ascii=False))
        return
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Validate basic structure (dict)
        if not isinstance(data, dict):
            data = {}
        _write_kv("tournaments", json.dumps(data, ensure_ascii=False))
    except Exception as e:
        print(f"Error migrating JSON to DB: {e}")
        _write_kv("tournaments", json.dumps({}, ensure_ascii=False))

def save_tournaments(tournaments: Dict[str, Tournament]):
    """Persist all tournaments to SQLite (as a single JSON blob)."""
    data = {
        tournament_id: tournament.to_dict()
        for tournament_id, tournament in tournaments.items()
    }
    try:
        ok = _write_kv("tournaments", json.dumps(data, ensure_ascii=False))
        return bool(ok)
    except Exception as e:
        print(f"Error saving tournaments: {e}")
        return False

def load_tournaments() -> Dict[str, Tournament]:
    """Load all tournaments from SQLite, migrating once from JSON if needed."""
    _migrate_json_to_db_if_needed()
    try:
        raw, _ = _read_kv("tournaments")
        if not raw:
            return {}
        data = json.loads(raw)
        tournaments = {}
        for tournament_id, tournament_data in data.items():
            tournament = Tournament.from_dict(tournament_data)
            tournaments[tournament_id] = tournament
        return tournaments
    except Exception as e:
        print(f"Error loading tournaments: {e}")
        return {}

def get_sport_icon(sport_type):
    """Get emoji icon for sport type"""
    icons = {
        "كرة قدم": "⚽",
        "كرة سلة": "🏀",
        "تنس": "🎾",
        "بينغ بونغ": "🏓"
    }
    return icons.get(sport_type, "🏆")

def get_round_name(round_type: str) -> str:
    """Get Arabic name for tournament round"""
    names = {
        "group": "دور المجموعات",
        "quarter": "ربع النهائي",
        "semi": "نصف النهائي",
        "final": "النهائي"
    }
    return names.get(round_type, round_type)

def validate_score(score_str: str) -> tuple[bool, int]:
    """Validate and convert score string to integer"""
    try:
        score = int(score_str)
        if score < 0:
            return False, 0
        return True, score
    except ValueError:
        return False, 0

def get_team_name_label(sport_type) -> str:
    """Get appropriate label for team/player name based on sport"""
    individual_sports = ["تنس", "بينغ بونغ"]
    if sport_type in individual_sports:
        return "اسم اللاعب"
    else:
        return "اسم الفريق"

def format_match_result(match, tournaments) -> str:
    """Format match result for display"""
    if not match.is_completed:
        return "لم تحدد النتيجة بعد"
    
    team1_name = "فريق غير معروف"
    team2_name = "فريق غير معروف"
    
    # Find tournament containing this match to get team names
    for tournament in tournaments.values():
        if match.id in tournament.matches or match.id in tournament.knockout_matches:
            team1_name = tournament.teams.get(match.team1_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
            team2_name = tournament.teams.get(match.team2_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
            break
    
    return f"{team1_name} {match.team1_score} - {match.team2_score} {team2_name}"
