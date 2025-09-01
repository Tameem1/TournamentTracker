import json
import os
from typing import Dict, List
from models import Tournament

DATA_FILE = "tournaments_data.json"

def save_tournaments(tournaments: Dict[str, Tournament]):
    """Save all tournaments to JSON file"""
    data = {
        tournament_id: tournament.to_dict() 
        for tournament_id, tournament in tournaments.items()
    }
    
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving tournaments: {e}")
        return False

def load_tournaments() -> Dict[str, Tournament]:
    """Load all tournaments from JSON file"""
    if not os.path.exists(DATA_FILE):
        return {}
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
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
