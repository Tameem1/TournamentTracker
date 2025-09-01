import streamlit as st
from typing import Dict, Optional
from models import Tournament, Team, Match, SportType, MatchStatus
from utils import save_tournaments, load_tournaments, get_sport_icon, get_round_name, validate_score, get_team_name_label

class TournamentManager:
    def __init__(self):
        if 'tournaments' not in st.session_state:
            st.session_state.tournaments = load_tournaments()
    
    def save_data(self):
        """Save current tournament data"""
        return save_tournaments(st.session_state.tournaments)
    
    def create_tournament(self, name: str, sport_type: SportType) -> bool:
        """Create a new tournament"""
        try:
            tournament = Tournament(
                id="",  # Will be auto-generated
                name=name,
                sport_type=sport_type
            )
            st.session_state.tournaments[tournament.id] = tournament
            self.save_data()
            return True
        except Exception as e:
            st.error(f"خطأ في إنشاء البطولة: {e}")
            return False
    
    def delete_tournament(self, tournament_id: str) -> bool:
        """Delete a tournament"""
        try:
            if tournament_id in st.session_state.tournaments:
                del st.session_state.tournaments[tournament_id]
                self.save_data()
                return True
            return False
        except Exception as e:
            st.error(f"خطأ في حذف البطولة: {e}")
            return False
    
    def add_team_to_tournament(self, tournament_id: str, team_name: str) -> bool:
        """Add team to tournament"""
        try:
            if tournament_id not in st.session_state.tournaments:
                return False
            
            tournament = st.session_state.tournaments[tournament_id]
            team = Team(
                id="",  # Will be auto-generated
                name=team_name,
                sport_type=tournament.sport_type
            )
            tournament.add_team(team)
            self.save_data()
            return True
        except Exception as e:
            st.error(f"خطأ في إضافة الفريق: {e}")
            return False
    
    def remove_team_from_tournament(self, tournament_id: str, team_id: str) -> bool:
        """Remove team from tournament"""
        try:
            if tournament_id not in st.session_state.tournaments:
                return False
            
            tournament = st.session_state.tournaments[tournament_id]
            tournament.remove_team(team_id)
            self.save_data()
            return True
        except Exception as e:
            st.error(f"خطأ في حذف الفريق: {e}")
            return False
    
    def create_groups_for_tournament(self, tournament_id: str, teams_per_group: int = 4) -> bool:
        """Create groups for tournament"""
        try:
            if tournament_id not in st.session_state.tournaments:
                return False
            
            tournament = st.session_state.tournaments[tournament_id]
            success = tournament.create_groups(teams_per_group)
            if success:
                tournament.generate_group_matches()
                self.save_data()
            return success
        except Exception as e:
            st.error(f"خطأ في إنشاء المجموعات: {e}")
            return False
    
    def update_match_result(self, tournament_id: str, match_id: str, team1_score: int, team2_score: int) -> bool:
        """Update match result"""
        try:
            if tournament_id not in st.session_state.tournaments:
                return False
            
            tournament = st.session_state.tournaments[tournament_id]
            
            # Check in group matches first
            if match_id in tournament.matches:
                match = tournament.matches[match_id]
                match.team1_score = team1_score
                match.team2_score = team2_score
                match.status = MatchStatus.COMPLETED
            # Check in knockout matches
            elif match_id in tournament.knockout_matches:
                match = tournament.knockout_matches[match_id]
                match.team1_score = team1_score
                match.team2_score = team2_score
                match.status = MatchStatus.COMPLETED
                # Advance knockout stage if needed
                tournament.advance_knockout_stage()
            else:
                return False
            
            self.save_data()
            return True
        except Exception as e:
            st.error(f"خطأ في تحديث النتيجة: {e}")
            return False
    
    def generate_knockout_for_tournament(self, tournament_id: str) -> bool:
        """Generate knockout stage for tournament"""
        try:
            if tournament_id not in st.session_state.tournaments:
                return False
            
            tournament = st.session_state.tournaments[tournament_id]
            success = tournament.generate_knockout_matches()
            if success:
                self.save_data()
            return success
        except Exception as e:
            st.error(f"خطأ في إنشاء دور الإقصاء: {e}")
            return False
    
    def get_tournament(self, tournament_id: str) -> Optional[Tournament]:
        """Get tournament by ID"""
        return st.session_state.tournaments.get(tournament_id)
    
    def get_all_tournaments(self) -> Dict[str, Tournament]:
        """Get all tournaments"""
        return st.session_state.tournaments
    
    def render_tournament_management(self):
        """Render tournament management interface"""
        st.header("⚙️ إدارة الدوريات")
        
        # Create new tournament
        with st.expander("إضافة دوري جديد", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                new_tournament_name = st.text_input("اسم الدوري")
            
            with col2:
                sport_options = [sport.value for sport in SportType]
                selected_sport = st.selectbox("نوع الرياضة", sport_options)
            
            if st.button("إنشاء الدوري", type="primary"):
                if new_tournament_name.strip():
                    sport_type = SportType(selected_sport)
                    if self.create_tournament(new_tournament_name.strip(), sport_type):
                        st.success("تم إنشاء الدوري بنجاح!")
                        st.rerun()
                    else:
                        st.error("فشل في إنشاء الدوري")
                else:
                    st.error("يرجى إدخال اسم الدوري")
        
        # Display existing tournaments
        tournaments = self.get_all_tournaments()
        if tournaments:
            st.subheader("الدوريات الحالية")
            
            for tournament_id, tournament in tournaments.items():
                with st.expander(f"{get_sport_icon(tournament.sport_type.value)} {tournament.name}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**النوع:** {tournament.sport_type.value}")
                        st.write(f"**عدد الفرق:** {len(tournament.teams)}")
                        st.write(f"**عدد المجموعات:** {len(tournament.groups)}")
                    
                    with col2:
                        st.write(f"**مباريات المجموعات:** {len(tournament.matches)}")
                        st.write(f"**مباريات الإقصاء:** {len(tournament.knockout_matches)}")
                        completed_matches = sum(1 for m in tournament.matches.values() if m.is_completed)
                        st.write(f"**المباريات المكتملة:** {completed_matches}")
                    
                    with col3:
                        if st.button(f"حذف الدوري", key=f"delete_{tournament_id}", type="secondary"):
                            if self.delete_tournament(tournament_id):
                                st.success("تم حذف الدوري بنجاح!")
                                st.rerun()
                        
                        if st.button(f"إدارة الفرق", key=f"manage_{tournament_id}", type="primary"):
                            st.session_state.current_tournament = tournament_id
                            st.session_state.page = "team_management"
                            st.rerun()
        else:
            st.info("لا توجد دوريات حالياً. قم بإنشاء دوري جديد.")
    
    def render_team_management(self, tournament_id: str):
        """Render team management interface"""
        tournament = self.get_tournament(tournament_id)
        if not tournament:
            st.error("الدوري غير موجود")
            return
        
        st.header(f"👥 إدارة الفرق - {tournament.name}")
        
        # Add new team
        with st.expander("إضافة فريق/لاعب جديد", expanded=False):
            team_name_label = get_team_name_label(tournament.sport_type.value)
            new_team_name = st.text_input(team_name_label)
            
            if st.button("إضافة", type="primary"):
                if new_team_name.strip():
                    if self.add_team_to_tournament(tournament_id, new_team_name.strip()):
                        st.success("تم إضافة الفريق بنجاح!")
                        st.rerun()
                    else:
                        st.error("فشل في إضافة الفريق")
                else:
                    st.error("يرجى إدخال اسم الفريق")
        
        # Display teams
        if tournament.teams:
            st.subheader("الفرق المسجلة")
            
            for team_id, team in tournament.teams.items():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{team.name}**")
                
                with col2:
                    if st.button("حذف", key=f"remove_team_{team_id}", type="secondary"):
                        if self.remove_team_from_tournament(tournament_id, team_id):
                            st.success("تم حذف الفريق بنجاح!")
                            st.rerun()
        
        # Group management
        st.subheader("إدارة المجموعات")
        
        if len(tournament.teams) >= 3:
            col1, col2 = st.columns(2)
            
            with col1:
                teams_per_group = st.selectbox("عدد الفرق في كل مجموعة", [3, 4], index=1)
            
            with col2:
                if st.button("إنشاء المجموعات", type="primary"):
                    if self.create_groups_for_tournament(tournament_id, teams_per_group):
                        st.success("تم إنشاء المجموعات بنجاح!")
                        st.rerun()
                    else:
                        st.error("فشل في إنشاء المجموعات")
        else:
            st.info("يجب إضافة 3 فرق على الأقل لإنشاء المجموعات")
        
        # Display groups
        if tournament.groups:
            st.subheader("المجموعات الحالية")
            
            for group_id, group in tournament.groups.items():
                with st.expander(group.name, expanded=True):
                    for team_id in group.team_ids:
                        if team_id in tournament.teams:
                            st.write(f"• {tournament.teams[team_id].name}")
        
        # Match management button
        if tournament.matches or tournament.knockout_matches:
            if st.button("إدارة المباريات", type="primary"):
                st.session_state.page = "match_management"
                st.rerun()
        
        # Back button
        if st.button("العودة للدوريات", type="secondary"):
            st.session_state.page = "tournament_management"
            if 'current_tournament' in st.session_state:
                del st.session_state.current_tournament
            st.rerun()
    
    def render_match_management(self, tournament_id: str):
        """Render match management interface"""
        tournament = self.get_tournament(tournament_id)
        if not tournament:
            st.error("الدوري غير موجود")
            return
        
        st.header(f"🤝 إدارة المباريات - {tournament.name}")
        
        # Group stage matches
        if tournament.matches:
            st.subheader("مباريات دور المجموعات")
            
            for group_id, group in tournament.groups.items():
                with st.expander(f"{group.name}", expanded=True):
                    group_matches = [m for m in tournament.matches.values() if m.group_id == group_id]
                    
                    if group_matches:
                        for match in group_matches:
                            self._render_match_form(tournament, match)
                    else:
                        st.info("لا توجد مباريات في هذه المجموعة")
        
        # Knockout stage
        if tournament.knockout_matches or tournament.can_generate_knockout():
            st.subheader("دور الإقصاء")
            
            if not tournament.knockout_matches and tournament.can_generate_knockout():
                if st.button("إنشاء دور الإقصاء", type="primary"):
                    if self.generate_knockout_for_tournament(tournament_id):
                        st.success("تم إنشاء دور الإقصاء بنجاح!")
                        st.rerun()
            
            if tournament.knockout_matches:
                # Group by round type
                rounds = {}
                for match in tournament.knockout_matches.values():
                    if match.round_type not in rounds:
                        rounds[match.round_type] = []
                    rounds[match.round_type].append(match)
                
                for round_type in ["semi", "final"]:
                    if round_type in rounds:
                        st.write(f"**{get_round_name(round_type)}**")
                        for match in rounds[round_type]:
                            self._render_match_form(tournament, match)
        
        # Back button
        if st.button("العودة لإدارة الفرق", type="secondary"):
            st.session_state.page = "team_management"
            st.rerun()
    
    def _render_match_form(self, tournament: Tournament, match: Match):
        """Render form for a single match"""
        team1_name = tournament.teams.get(match.team1_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
        team2_name = tournament.teams.get(match.team2_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        
        with col1:
            st.write(team1_name)
        
        with col2:
            team1_score = st.number_input(
                "النتيجة",
                min_value=0,
                value=match.team1_score if match.team1_score is not None else 0,
                key=f"team1_score_{match.id}",
                label_visibility="collapsed"
            )
        
        with col3:
            st.write("VS")
        
        with col4:
            team2_score = st.number_input(
                "النتيجة",
                min_value=0,
                value=match.team2_score if match.team2_score is not None else 0,
                key=f"team2_score_{match.id}",
                label_visibility="collapsed"
            )
        
        with col5:
            st.write(team2_name)
        
        col6, col7 = st.columns([1, 1])
        
        with col6:
            if st.button("تحديث النتيجة", key=f"update_{match.id}", type="primary"):
                if self.update_match_result(tournament.id, match.id, team1_score, team2_score):
                    st.success("تم تحديث النتيجة بنجاح!")
                    st.rerun()
        
        with col7:
            if match.is_completed:
                st.success("مكتملة")
            else:
                st.warning("معلقة")
        
        st.divider()
