from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum
import json
import uuid

class SportType(Enum):
    FOOTBALL = "كرة قدم"
    BASKETBALL = "كرة سلة"
    TENNIS = "تنس"
    PING_PONG = "بينغ بونغ"

class MatchStatus(Enum):
    PENDING = "معلقة"
    COMPLETED = "مكتملة"

@dataclass
class Team:
    id: str
    name: str
    sport_type: SportType
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class Match:
    id: str
    team1_id: str
    team2_id: str
    team1_score: Optional[int] = None
    team2_score: Optional[int] = None
    status: MatchStatus = MatchStatus.PENDING
    group_id: Optional[str] = None
    round_type: str = "group"  # "group", "quarter", "semi", "final"
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    @property
    def is_completed(self) -> bool:
        return self.status == MatchStatus.COMPLETED and self.team1_score is not None and self.team2_score is not None
    
    def get_winner(self) -> Optional[str]:
        if not self.is_completed:
            return None
        if self.team1_score > self.team2_score:
            return self.team1_id
        elif self.team2_score > self.team1_score:
            return self.team2_id
        return None  # Draw
    
    def is_draw(self) -> bool:
        return self.is_completed and self.team1_score == self.team2_score

@dataclass
class Group:
    id: str
    name: str
    team_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class Tournament:
    id: str
    name: str
    sport_type: SportType
    teams: Dict[str, Team] = field(default_factory=dict)
    groups: Dict[str, Group] = field(default_factory=dict)
    matches: Dict[str, Match] = field(default_factory=dict)
    knockout_matches: Dict[str, Match] = field(default_factory=dict)
    is_active: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def add_team(self, team: Team):
        self.teams[team.id] = team
    
    def remove_team(self, team_id: str):
        if team_id in self.teams:
            del self.teams[team_id]
            # Remove from groups
            for group in self.groups.values():
                if team_id in group.team_ids:
                    group.team_ids.remove(team_id)
    
    def create_groups(self, teams_per_group: int = 4):
        """Create groups with specified number of teams per group"""
        self.groups.clear()
        team_list = list(self.teams.keys())
        
        if len(team_list) < 3:
            return False
            
        group_count = max(1, len(team_list) // teams_per_group)
        if len(team_list) % teams_per_group != 0:
            group_count += 1
            
        for i in range(group_count):
            group = Group(
                id=str(uuid.uuid4()),
                name=f"المجموعة {chr(65 + i)}"  # Group A, B, C...
            )
            self.groups[group.id] = group
            
        # Distribute teams among groups
        for i, team_id in enumerate(team_list):
            group_index = i % group_count
            group_id = list(self.groups.keys())[group_index]
            self.groups[group_id].team_ids.append(team_id)
            
        return True
    
    def generate_group_matches(self):
        """Generate all possible matches within each group"""
        self.matches.clear()
        
        for group in self.groups.values():
            team_ids = group.team_ids
            # Generate round-robin matches for the group
            for i in range(len(team_ids)):
                for j in range(i + 1, len(team_ids)):
                    match = Match(
                        id=str(uuid.uuid4()),
                        team1_id=team_ids[i],
                        team2_id=team_ids[j],
                        group_id=group.id,
                        round_type="group"
                    )
                    self.matches[match.id] = match
    
    def get_group_standings(self, group_id: str) -> List[Dict]:
        """Calculate standings for a specific group"""
        if group_id not in self.groups:
            return []
            
        group = self.groups[group_id]
        standings = {}
        
        # Initialize standings for all teams in group
        for team_id in group.team_ids:
            standings[team_id] = {
                'team_id': team_id,
                'team_name': self.teams[team_id].name,
                'played': 0,
                'won': 0,
                'drawn': 0,
                'lost': 0,
                'goals_for': 0,
                'goals_against': 0,
                'goal_difference': 0,
                'points': 0
            }
        
        # Calculate stats from completed matches
        for match in self.matches.values():
            if match.group_id == group_id and match.is_completed:
                team1_stats = standings[match.team1_id]
                team2_stats = standings[match.team2_id]
                
                team1_stats['played'] += 1
                team2_stats['played'] += 1
                team1_stats['goals_for'] += match.team1_score
                team1_stats['goals_against'] += match.team2_score
                team2_stats['goals_for'] += match.team2_score
                team2_stats['goals_against'] += match.team1_score
                
                if match.team1_score > match.team2_score:
                    team1_stats['won'] += 1
                    team1_stats['points'] += 3
                    team2_stats['lost'] += 1
                elif match.team2_score > match.team1_score:
                    team2_stats['won'] += 1
                    team2_stats['points'] += 3
                    team1_stats['lost'] += 1
                else:
                    team1_stats['drawn'] += 1
                    team2_stats['drawn'] += 1
                    team1_stats['points'] += 1
                    team2_stats['points'] += 1
                
                team1_stats['goal_difference'] = team1_stats['goals_for'] - team1_stats['goals_against']
                team2_stats['goal_difference'] = team2_stats['goals_for'] - team2_stats['goals_against']
        
        # Sort by points, then goal difference, then goals for
        sorted_standings = sorted(
            standings.values(),
            key=lambda x: (x['points'], x['goal_difference'], x['goals_for']),
            reverse=True
        )
        
        return sorted_standings
    
    def get_group_winners(self) -> List[str]:
        """Get the winner from each group"""
        winners = []
        for group_id in self.groups.keys():
            standings = self.get_group_standings(group_id)
            if standings:
                winners.append(standings[0]['team_id'])
        return winners
    
    def can_generate_knockout(self) -> bool:
        """Check if knockout stage can be generated"""
        winners = self.get_group_winners()
        return len(winners) >= 2
    
    def generate_knockout_matches(self):
        """Generate knockout stage matches"""
        winners = self.get_group_winners()
        if len(winners) < 2:
            return False
            
        self.knockout_matches.clear()
        
        if len(winners) == 2:
            # Direct final
            final_match = Match(
                id=str(uuid.uuid4()),
                team1_id=winners[0],
                team2_id=winners[1],
                round_type="final"
            )
            self.knockout_matches[final_match.id] = final_match
        elif len(winners) == 4:
            # Semi-finals
            semi1 = Match(
                id=str(uuid.uuid4()),
                team1_id=winners[0],
                team2_id=winners[3],
                round_type="semi"
            )
            semi2 = Match(
                id=str(uuid.uuid4()),
                team1_id=winners[1],
                team2_id=winners[2],
                round_type="semi"
            )
            self.knockout_matches[semi1.id] = semi1
            self.knockout_matches[semi2.id] = semi2
        
        return True
    
    def advance_knockout_stage(self):
        """Advance completed knockout matches to next round"""
        semi_winners = []
        
        for match in self.knockout_matches.values():
            if match.round_type == "semi" and match.is_completed:
                winner = match.get_winner()
                if winner:
                    semi_winners.append(winner)
        
        if len(semi_winners) == 2:
            # Create final match
            final_exists = any(m.round_type == "final" for m in self.knockout_matches.values())
            if not final_exists:
                final_match = Match(
                    id=str(uuid.uuid4()),
                    team1_id=semi_winners[0],
                    team2_id=semi_winners[1],
                    round_type="final"
                )
                self.knockout_matches[final_match.id] = final_match

    def to_dict(self) -> dict:
        """Convert tournament to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'sport_type': self.sport_type.value,
            'is_active': self.is_active,
            'teams': {k: {
                'id': v.id,
                'name': v.name,
                'sport_type': v.sport_type.value
            } for k, v in self.teams.items()},
            'groups': {k: {
                'id': v.id,
                'name': v.name,
                'team_ids': v.team_ids
            } for k, v in self.groups.items()},
            'matches': {k: {
                'id': v.id,
                'team1_id': v.team1_id,
                'team2_id': v.team2_id,
                'team1_score': v.team1_score,
                'team2_score': v.team2_score,
                'status': v.status.value,
                'group_id': v.group_id,
                'round_type': v.round_type
            } for k, v in self.matches.items()},
            'knockout_matches': {k: {
                'id': v.id,
                'team1_id': v.team1_id,
                'team2_id': v.team2_id,
                'team1_score': v.team1_score,
                'team2_score': v.team2_score,
                'status': v.status.value,
                'group_id': v.group_id,
                'round_type': v.round_type
            } for k, v in self.knockout_matches.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Tournament':
        """Create tournament from dictionary"""
        tournament = cls(
            id=data['id'],
            name=data['name'],
            sport_type=SportType(data['sport_type']),
            is_active=data.get('is_active', True)
        )
        
        # Load teams
        for team_data in data.get('teams', {}).values():
            team = Team(
                id=team_data['id'],
                name=team_data['name'],
                sport_type=SportType(team_data['sport_type'])
            )
            tournament.teams[team.id] = team
        
        # Load groups
        for group_data in data.get('groups', {}).values():
            group = Group(
                id=group_data['id'],
                name=group_data['name'],
                team_ids=group_data['team_ids']
            )
            tournament.groups[group.id] = group
        
        # Load matches
        for match_data in data.get('matches', {}).values():
            match = Match(
                id=match_data['id'],
                team1_id=match_data['team1_id'],
                team2_id=match_data['team2_id'],
                team1_score=match_data['team1_score'],
                team2_score=match_data['team2_score'],
                status=MatchStatus(match_data['status']),
                group_id=match_data.get('group_id'),
                round_type=match_data.get('round_type', 'group')
            )
            tournament.matches[match.id] = match
        
        # Load knockout matches
        for match_data in data.get('knockout_matches', {}).values():
            match = Match(
                id=match_data['id'],
                team1_id=match_data['team1_id'],
                team2_id=match_data['team2_id'],
                team1_score=match_data['team1_score'],
                team2_score=match_data['team2_score'],
                status=MatchStatus(match_data['status']),
                group_id=match_data.get('group_id'),
                round_type=match_data.get('round_type', 'knockout')
            )
            tournament.knockout_matches[match.id] = match
        
        # Normalize knockout round types if missing/unknown to ensure proper display
        if tournament.knockout_matches:
            valid_rounds = {"semi", "final"}
            unknown = [m for m in tournament.knockout_matches.values() if m.round_type not in valid_rounds]
            if unknown:
                total_knock = len(tournament.knockout_matches)
                inferred_round = "final" if total_knock == 1 else ("semi" if total_knock == 2 else None)
                if inferred_round:
                    for m in unknown:
                        m.round_type = inferred_round
                else:
                    # Fallback: default unknown to 'semi' so they are at least visible
                    for m in unknown:
                        m.round_type = "semi"

        return tournament
