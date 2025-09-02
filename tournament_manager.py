import streamlit as st
import os
from typing import Dict, Optional
from models import Tournament, Team, Match, SportType, MatchStatus
from utils import save_tournaments, load_tournaments, get_sport_icon, get_round_name, validate_score, get_team_name_label, get_store_mtime

class TournamentManager:
    def __init__(self):
        if 'tournaments' not in st.session_state:
            st.session_state.tournaments = load_tournaments()
        # Track data file modification time to auto-refresh
        if '_data_mtime' not in st.session_state:
            try:
                st.session_state._data_mtime = float(get_store_mtime())
            except Exception:
                st.session_state._data_mtime = 0.0

    def _refresh_if_changed(self):
        """Reload tournaments from disk if the data file has changed externally."""
        try:
            current_mtime = float(get_store_mtime())
        except Exception:
            current_mtime = 0.0
        if current_mtime and current_mtime > st.session_state.get('_data_mtime', 0.0):
            st.session_state.tournaments = load_tournaments()
            st.session_state._data_mtime = current_mtime
    
    def save_data(self):
        """Save current tournament data"""
        ok = save_tournaments(st.session_state.tournaments)
        # Update mtime after save
        try:
            st.session_state._data_mtime = float(get_store_mtime())
        except Exception:
            pass
        return ok
    
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
    
    def create_custom_groups_for_tournament(self, tournament_id: str, group_sizes: list[int]) -> bool:
        """Create groups with custom sizes for tournament"""
        try:
            if tournament_id not in st.session_state.tournaments:
                return False
            
            tournament = st.session_state.tournaments[tournament_id]
            success = tournament.create_custom_groups(group_sizes)
            if success:
                tournament.generate_group_matches()
                self.save_data()
            return success
        except Exception as e:
            st.error(f"خطأ في إنشاء المجموعات المخصصة: {e}")
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
        # Auto-refresh if file changed (e.g., another session updated results)
        self._refresh_if_changed()
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
            
            if st.button("إضافة", type="primary", use_container_width=True):
                if new_team_name.strip():
                    if self.add_team_to_tournament(tournament_id, new_team_name.strip()):
                        st.success("تم إضافة الفريق بنجاح!")
                        st.rerun()
                    else:
                        st.error("فشل في إضافة الفريق")
                else:
                    st.error("يرجى إدخال اسم الفريق")

        # Bulk add teams
        with st.expander("إضافة عدة فرق دفعة واحدة", expanded=False):
            st.caption("أدخل كل اسم في سطر منفصل")
            bulk_text = st.text_area("الأسماء", height=150, key="bulk_team_text_manage")
            if st.button("إضافة الكل", type="primary", key="bulk_add_btn_manage", use_container_width=True):
                names = [n.strip() for n in bulk_text.splitlines() if n.strip()]
                if not names:
                    st.warning("لم يتم العثور على أسماء.")
                else:
                    success_count = 0
                    for name in names:
                        if self.add_team_to_tournament(tournament_id, name):
                            success_count += 1
                    st.success(f"تمت إضافة {success_count} من {len(names)}.")
                    st.rerun()
        
        # Display teams
        if tournament.teams:
            st.subheader("الفرق المسجلة")
            search_query = st.text_input("ابحث عن فريق", key="team_search_manage")
            # Preserve insertion order; only filter
            for team_id, team in tournament.teams.items():
                if search_query and search_query.strip() not in team.name:
                    continue
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{team.name}**")
                
                with col2:
                    if st.button("حذف", key=f"remove_team_{team_id}", type="secondary", use_container_width=True):
                        if self.remove_team_from_tournament(tournament_id, team_id):
                            st.success("تم حذف الفريق بنجاح!")
                            st.rerun()
        
        # Group management
        st.subheader("إدارة المجموعات")
        
        if len(tournament.teams) >= 3:
            group_mode = st.radio("طريقة إنشاء المجموعات", ["حجم موحد", "أحجام مخصصة"], horizontal=True, key="group_mode_manage")
            
            if group_mode == "حجم موحد":
                col1, col2 = st.columns(2)
                
                with col1:
                    teams_per_group = st.selectbox("عدد الفرق في كل مجموعة", [2, 3, 4, 5, 6], index=2)
                
                with col2:
                    if st.button("إنشاء المجموعات", type="primary", use_container_width=True):
                        if self.create_groups_for_tournament(tournament_id, teams_per_group):
                            st.success("تم إنشاء المجموعات بنجاح!")
                            st.rerun()
                        else:
                            st.error("فشل في إنشاء المجموعات")
            else:
                st.write(f"**إجمالي الفرق:** {len(tournament.teams)}")
                st.caption("أدخل عدد الفرق لكل مجموعة (يجب أن يساوي إجمالي الفرق)")
                
                # Dynamic group size inputs
                num_groups = st.number_input("عدد المجموعات", min_value=2, max_value=len(tournament.teams), value=2, key="num_groups_manage")
                
                group_sizes = []
                cols = st.columns(min(4, num_groups))
                
                for i in range(num_groups):
                    with cols[i % len(cols)]:
                        size = st.number_input(
                            f"المجموعة {chr(65 + i)}", 
                            min_value=1, 
                            max_value=len(tournament.teams), 
                            value=2 if i < 2 else 1,
                            key=f"group_size_manage_{i}"
                        )
                        group_sizes.append(size)
                
                total_specified = sum(group_sizes)
                st.write(f"**المجموع المحدد:** {total_specified} / {len(tournament.teams)}")
                
                if total_specified == len(tournament.teams):
                    if st.button("إنشاء المجموعات المخصصة", type="primary", use_container_width=True):
                        if self.create_custom_groups_for_tournament(tournament_id, group_sizes):
                            st.success("تم إنشاء المجموعات المخصصة بنجاح!")
                            st.rerun()
                        else:
                            st.error("فشل في إنشاء المجموعات المخصصة")
                else:
                    st.error(f"المجموع يجب أن يساوي {len(tournament.teams)}")
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
            if st.button("إدارة المباريات", type="primary", use_container_width=True):
                st.session_state.page = "match_management"
                st.rerun()
        
        # Back button
        if st.button("العودة للدوريات", type="secondary", use_container_width=True):
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

        # Manual match creation
        with st.expander("إنشاء مباراة يدويًا", expanded=False):
            round_label = st.selectbox("نوع الجولة", ["دور المجموعات", "نصف النهائي", "النهائي"], index=0, key="mm_round_type")
            round_map = {
                "دور المجموعات": "group",
                "نصف النهائي": "semi",
                "النهائي": "final",
            }
            round_type = round_map[round_label]

            selected_group_id = None
            if round_type == "group":
                group_options = {grp.name: gid for gid, grp in tournament.groups.items()}
                if not group_options:
                    st.info("لا توجد مجموعات. أنشئ المجموعات أولاً.")
                else:
                    group_label = st.selectbox("المجموعة", list(group_options.keys()), key="mm_manual_group")
                    selected_group_id = group_options[group_label]

            # Team options (restrict to group if group selected)
            if round_type == "group" and selected_group_id:
                team_ids = tournament.groups[selected_group_id].team_ids
            else:
                team_ids = list(tournament.teams.keys())

            team_name_map = {tournament.teams[tid].name: tid for tid in team_ids if tid in tournament.teams}
            if not team_name_map:
                st.info("لا توجد فرق متاحة للاختيار.")
            else:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    team1_label = st.selectbox("الفريق 1", list(team_name_map.keys()), key="mm_manual_t1")
                with col_t2:
                    team2_label = st.selectbox("الفريق 2", list(team_name_map.keys()), key="mm_manual_t2")

                create_col1, create_col2 = st.columns([1,3])
                with create_col1:
                    if st.button("إنشاء المباراة", type="primary", use_container_width=True, key="mm_manual_create"):
                        if team1_label == team2_label:
                            st.error("لا يمكن اختيار نفس الفريق مرتين")
                        else:
                            ok, msg = self.create_manual_match(
                                tournament_id,
                                team_name_map[team1_label],
                                team_name_map[team2_label],
                                round_type,
                                selected_group_id,
                            )
                            if ok:
                                st.success("تم إنشاء المباراة بنجاح!")
                                st.rerun()
                            else:
                                st.error(msg or "فشل في إنشاء المباراة")
        
        # Group stage matches
        if tournament.matches:
            st.subheader("مباريات دور المجموعات")

            # Filters
            filter_cols = st.columns([2, 2, 2])
            with filter_cols[0]:
                group_filter_options = {"كل المجموعات": None}
                for gid, grp in tournament.groups.items():
                    group_filter_options[grp.name] = gid
                selected_group_label = st.selectbox("المجموعة", list(group_filter_options.keys()), key="mm_group_filter")
                selected_group_id = group_filter_options[selected_group_label]
            with filter_cols[1]:
                status_filter_label = st.selectbox("الحالة", ["الكل", "معلقة فقط", "مكتملة فقط"], key="mm_status_filter")
            with filter_cols[2]:
                team_search = st.text_input("بحث عن فريق", key="mm_team_search")

            # Render by groups
            for group_id, group in tournament.groups.items():
                if selected_group_id and group_id != selected_group_id:
                    continue
                with st.expander(f"{group.name}", expanded=True):
                    group_matches = [m for m in tournament.matches.values() if m.group_id == group_id]
                    if team_search:
                        team_search_stripped = team_search.strip()
                        def match_has_team(m):
                            n1 = tournament.teams.get(m.team1_id).name if m.team1_id in tournament.teams else ""
                            n2 = tournament.teams.get(m.team2_id).name if m.team2_id in tournament.teams else ""
                            return team_search_stripped in n1 or team_search_stripped in n2
                        group_matches = [m for m in group_matches if match_has_team(m)]
                    if status_filter_label == "معلقة فقط":
                        group_matches = [m for m in group_matches if not m.is_completed]
                    elif status_filter_label == "مكتملة فقط":
                        group_matches = [m for m in group_matches if m.is_completed]

                    if group_matches:
                        for match in group_matches:
                            self._render_match_form(tournament, match)
                    else:
                        st.info("لا توجد مباريات مطابقة للمرشح")
        
        # Knockout stage
        if tournament.knockout_matches or tournament.can_generate_knockout():
            st.subheader("دور الإقصاء")
            
            if not tournament.knockout_matches and tournament.can_generate_knockout():
                if st.button("إنشاء دور الإقصاء", type="primary", use_container_width=True):
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
        if st.button("العودة لإدارة الفرق", type="secondary", use_container_width=True):
            st.session_state.page = "team_management"
            st.rerun()

    def create_manual_match(self, tournament_id: str, team1_id: str, team2_id: str, round_type: str = "group", group_id: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """Create a manual match between two teams. Avoid duplicates.

        Returns (ok, error_message). error_message is None when ok is True.
        """
        try:
            tournaments = self.get_all_tournaments()
            if tournament_id not in tournaments:
                return False, "الدوري غير موجود"
            tournament = tournaments[tournament_id]

            if team1_id == team2_id:
                return False, "لا يمكن اختيار نفس الفريق"
            if team1_id not in tournament.teams or team2_id not in tournament.teams:
                return False, "فرق غير صالحة"

            from models import Match

            if round_type == "group":
                if not group_id or group_id not in tournament.groups:
                    return False, "المجموعة غير صالحة"
                # Ensure both teams in the selected group
                group_team_ids = set(tournament.groups[group_id].team_ids)
                if team1_id not in group_team_ids or team2_id not in group_team_ids:
                    return False, "الفريقان يجب أن يكونا ضمن نفس المجموعة"
                # Check duplicates in group matches (order-insensitive)
                for m in tournament.matches.values():
                    if m.group_id == group_id and {m.team1_id, m.team2_id} == {team1_id, team2_id}:
                        return False, "المباراة موجودة بالفعل في هذه المجموعة"
                new_match = Match(id="", team1_id=team1_id, team2_id=team2_id, group_id=group_id, round_type="group")
                tournament.matches[new_match.id] = new_match
            else:
                # Knockout rounds
                if round_type not in {"semi", "final"}:
                    return False, "نوع الجولة غير صالح"
                # Prevent duplicates in knockout with same pairing and round
                for m in tournament.knockout_matches.values():
                    if m.round_type == round_type and {m.team1_id, m.team2_id} == {team1_id, team2_id}:
                        return False, "المباراة موجودة بالفعل في هذا الدور"
                new_match = Match(id="", team1_id=team1_id, team2_id=team2_id, round_type=round_type)
                tournament.knockout_matches[new_match.id] = new_match

            self.save_data()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def update_match_competitors(self, tournament_id: str, match_id: str, team1_id: str, team2_id: str) -> tuple[bool, Optional[str]]:
        """Update competitors for an existing match with validation.

        Resets scores and status to معلقة.
        Returns (ok, error_message).
        """
        try:
            tournaments = self.get_all_tournaments()
            if tournament_id not in tournaments:
                return False, "الدوري غير موجود"
            tournament = tournaments[tournament_id]

            # Locate match
            match: Optional[Match]
            in_group = False
            if match_id in tournament.matches:
                match = tournament.matches[match_id]
                in_group = True
            elif match_id in tournament.knockout_matches:
                match = tournament.knockout_matches[match_id]
            else:
                return False, "المباراة غير موجودة"

            if team1_id == team2_id:
                return False, "لا يمكن اختيار نفس الفريق"
            if team1_id not in tournament.teams or team2_id not in tournament.teams:
                return False, "فرق غير صالحة"

            # Group validation
            if in_group:
                gid = match.group_id
                if not gid or gid not in tournament.groups:
                    return False, "المجموعة غير صالحة"
                group_team_ids = set(tournament.groups[gid].team_ids)
                if team1_id not in group_team_ids or team2_id not in group_team_ids:
                    return False, "الفريقان يجب أن يكونا ضمن نفس المجموعة"
                # Duplicate check among group matches excluding self
                for m in tournament.matches.values():
                    if m.id == match.id:
                        continue
                    if m.group_id == gid and {m.team1_id, m.team2_id} == {team1_id, team2_id}:
                        return False, "مباراة بنفس المتنافسين موجودة بالفعل في هذه المجموعة"
            else:
                # Knockout duplicate check (same round)
                rtype = match.round_type
                for m in tournament.knockout_matches.values():
                    if m.id == match.id:
                        continue
                    if m.round_type == rtype and {m.team1_id, m.team2_id} == {team1_id, team2_id}:
                        return False, "مباراة بنفس المتنافسين موجودة بالفعل في هذا الدور"

            # Apply update and reset scores
            match.team1_id = team1_id
            match.team2_id = team2_id
            match.team1_score = None
            match.team2_score = None
            match.status = MatchStatus.PENDING

            self.save_data()
            return True, None
        except Exception as e:
            return False, str(e)

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
            if st.button("تحديث النتيجة", key=f"update_{match.id}", type="primary", use_container_width=True):
                if self.update_match_result(tournament.id, match.id, team1_score, team2_score):
                    st.success("تم تحديث النتيجة بنجاح!")
                    st.rerun()
        
        with col7:
            if match.is_completed:
                st.success("مكتملة")
            else:
                st.warning("معلقة")

        # In-place competitor editing
        with st.expander("تعديل المتنافسين", expanded=False):
            # Determine allowed teams
            if match.round_type == "group" and match.group_id in tournament.groups:
                allowed_ids = list(tournament.groups[match.group_id].team_ids)
            else:
                allowed_ids = list(tournament.teams.keys())

            options = [tournament.teams[tid].name for tid in allowed_ids if tid in tournament.teams]
            id_by_name = {tournament.teams[tid].name: tid for tid in allowed_ids if tid in tournament.teams}

            # Preselect current teams
            def _safe_index(items, value):
                try:
                    return items.index(value)
                except ValueError:
                    return 0 if items else 0

            col_a, col_b = st.columns(2)
            with col_a:
                sel_t1 = st.selectbox("الفريق 1", options, index=_safe_index(options, team1_name), key=f"edit_t1_{match.id}")
            with col_b:
                sel_t2 = st.selectbox("الفريق 2", options, index=_safe_index(options, team2_name), key=f"edit_t2_{match.id}")

            save_col, note_col = st.columns([1,3])
            with save_col:
                if st.button("حفظ المتنافسين", type="primary", use_container_width=True, key=f"save_comp_{match.id}"):
                    if sel_t1 == sel_t2:
                        st.error("لا يمكن اختيار نفس الفريق")
                    else:
                        ok, msg = self.update_match_competitors(
                            tournament.id,
                            match.id,
                            id_by_name.get(sel_t1, ""),
                            id_by_name.get(sel_t2, ""),
                        )
                        if ok:
                            st.success("تم تحديث المتنافسين! تم تصفير النتيجة للحفاظ على الاتساق.")
                            st.rerun()
                        else:
                            st.error(msg or "فشل في تحديث المتنافسين")
            with note_col:
                st.caption("تغيير المتنافسين يعيد تعيين النتيجة إلى معلّقة بدون أهداف.")
        
        # Quick actions
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            if st.button(f"🏆 فوز {team1_name}", key=f"qa_t1_{match.id}", type="secondary", use_container_width=True):
                if self.update_match_result(tournament.id, match.id, 1, 0):
                    st.success("تم تسجيل النتيجة")
                    st.rerun()
        with qa2:
            if st.button("🤝 تعادل", key=f"qa_draw_{match.id}", type="secondary", use_container_width=True):
                if self.update_match_result(tournament.id, match.id, 0, 0):
                    st.success("تم تسجيل التعادل")
                    st.rerun()
        with qa3:
            if st.button(f"🏆 فوز {team2_name}", key=f"qa_t2_{match.id}", type="secondary", use_container_width=True):
                if self.update_match_result(tournament.id, match.id, 0, 1):
                    st.success("تم تسجيل النتيجة")
                    st.rerun()

        st.divider()
