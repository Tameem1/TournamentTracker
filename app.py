import streamlit as st
import time
from tournament_manager import TournamentManager
from utils import get_sport_icon, get_round_name, get_team_name_label
from models import SportType

# Configure page
st.set_page_config(
    page_title="دوريات نادي الأمين",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize tournament manager
tm = TournamentManager()

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "dashboard"
if 'viewing_mode' not in st.session_state:
    st.session_state.viewing_mode = "manual"
if 'slideshow_interval' not in st.session_state:
    st.session_state.slideshow_interval = 10
if 'current_slide' not in st.session_state:
    st.session_state.current_slide = 0
if 'auto_mode_running' not in st.session_state:
    st.session_state.auto_mode_running = False

def render_add_results_page():
    """Render add results page"""
    st.title("📝 أضف نتائج")
    
    tournaments = tm.get_all_tournaments()
    
    if not tournaments:
        st.warning("لا توجد دوريات متاحة. يجب إنشاء دوري وإضافة فرق أولاً.")
        return
    
    # Get all pending matches from all tournaments
    pending_matches = []
    for tournament_id, tournament in tournaments.items():
        # Group stage matches
        for match_id, match in tournament.matches.items():
            if not match.is_completed:
                pending_matches.append({
                    'tournament_id': tournament_id,
                    'tournament_name': tournament.name,
                    'match_id': match_id,
                    'match': match,
                    'stage': 'group'
                })
        # Knockout matches
        for match_id, match in tournament.knockout_matches.items():
            if not match.is_completed:
                pending_matches.append({
                    'tournament_id': tournament_id,
                    'tournament_name': tournament.name,
                    'match_id': match_id,
                    'match': match,
                    'stage': 'knockout'
                })
    
    if not pending_matches:
        st.info("جميع المباريات مكتملة! لا توجد مباريات معلقة.")
        return
    
    st.subheader("اختر المباراة لإدخال النتيجة")
    
    # Create match options for selectbox
    match_options = {}
    for item in pending_matches:
        tournament = tournaments[item['tournament_id']]
        team1 = tournament.teams.get(item['match'].team1_id)
        team2 = tournament.teams.get(item['match'].team2_id)
        team1_name = team1.name if team1 else 'فريق غير معروف'
        team2_name = team2.name if team2 else 'فريق غير معروف'
        stage_name = "دور المجموعات" if item['stage'] == 'group' else get_round_name(item['match'].round_type)
        
        match_label = f"{item['tournament_name']} - {stage_name}: {team1_name} ضد {team2_name}"
        match_options[match_label] = item
    
    selected_match_label = st.selectbox("المباراة", list(match_options.keys()))
    
    if selected_match_label:
        selected_item = match_options[selected_match_label]
        tournament = tournaments[selected_item['tournament_id']]
        match = selected_item['match']
        
        team1 = tournament.teams.get(match.team1_id)
        team2 = tournament.teams.get(match.team2_id)
        team1_name = team1.name if team1 else 'فريق غير معروف'
        team2_name = team2.name if team2 else 'فريق غير معروف'
        
        st.markdown("---")
        st.subheader(f"نتيجة المباراة: {team1_name} ضد {team2_name}")
        
        # Simple result selection (win/loss/draw)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"🏆 فوز {team1_name}", key="team1_win", width="stretch", type="primary"):
                # Team 1 wins: 1-0
                if tm.update_match_result(selected_item['tournament_id'], match.id, 1, 0):
                    st.success(f"تم تسجيل فوز {team1_name}!")
                    st.rerun()
                else:
                    st.error("فشل في تحديث النتيجة")
        
        with col2:
            if st.button("🤝 تعادل", key="draw", width="stretch", type="secondary"):
                # Draw: 0-0
                if tm.update_match_result(selected_item['tournament_id'], match.id, 0, 0):
                    st.success("تم تسجيل التعادل!")
                    st.rerun()
                else:
                    st.error("فشل في تحديث النتيجة")
        
        with col3:
            if st.button(f"🏆 فوز {team2_name}", key="team2_win", width="stretch", type="primary"):
                # Team 2 wins: 0-1
                if tm.update_match_result(selected_item['tournament_id'], match.id, 0, 1):
                    st.success(f"تم تسجيل فوز {team2_name}!")
                    st.rerun()
                else:
                    st.error("فشل في تحديث النتيجة")

def render_view_results_page():
    """Render view results page"""
    st.title("📺 عرض نتائج")
    
    tournaments = tm.get_all_tournaments()
    
    if not tournaments:
        st.info("لا توجد دوريات متاحة للعرض.")
        return
    
    # Viewing mode selection
    col1, col2 = st.columns(2)
    
    with col1:
        viewing_mode = st.radio(
            "طريقة العرض",
            ["manual", "automatic"],
            format_func=lambda x: "يدوي" if x == "manual" else "تلقائي",
            index=0 if st.session_state.viewing_mode == "manual" else 1
        )
        st.session_state.viewing_mode = viewing_mode
    
    with col2:
        if viewing_mode == "automatic":
            interval = st.slider(
                "مدة العرض (ثواني)",
                min_value=5,
                max_value=60,
                value=st.session_state.slideshow_interval,
                step=5
            )
            st.session_state.slideshow_interval = interval
    
    st.markdown("---")
    
    if viewing_mode == "manual":
        # Manual viewing mode
        st.subheader("اختر الدوري للعرض")
        
        tournament_options = {f"{get_sport_icon(t.sport_type.value)} {t.name}": t.id for t in tournaments.values()}
        selected_tournament_label = st.selectbox("الدوري", list(tournament_options.keys()))
        
        if selected_tournament_label:
            selected_tournament_id = tournament_options[selected_tournament_label]
            selected_tournament = tournaments[selected_tournament_id]
            
            # Control buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🖥️ عرض كامل", type="primary", key="full_screen_btn"):
                    st.session_state.full_screen_mode = True
                    st.session_state.full_screen_tournament = selected_tournament_id
                    st.rerun()
            
            with col2:
                if st.button("⚙️ تعديل هذا الدوري", type="secondary"):
                    st.session_state.current_tournament = selected_tournament_id
                    st.session_state.page = "team_management"
                    st.rerun()
            
            with col3:
                if 'full_screen_mode' in st.session_state and st.session_state.full_screen_mode:
                    if st.button("🔙 عرض عادي", type="secondary", key="normal_screen_btn"):
                        st.session_state.full_screen_mode = False
                        if 'full_screen_tournament' in st.session_state:
                            del st.session_state.full_screen_tournament
                        st.rerun()
            
            st.markdown("---")
            
            # Display tournament in appropriate mode
            if 'full_screen_mode' in st.session_state and st.session_state.full_screen_mode and st.session_state.get('full_screen_tournament') == selected_tournament_id:
                render_tournament_display(selected_tournament, full_screen=True)
            else:
                render_tournament_display(selected_tournament, full_screen=False)
    
    else:
        # Automatic viewing mode
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ بدء العرض التلقائي", type="primary"):
                st.session_state.auto_mode_running = True
                st.rerun()
        
        with col2:
            if st.button("⏹️ إيقاف العرض التلقائي", type="secondary"):
                st.session_state.auto_mode_running = False
                st.rerun()
        
        if st.session_state.auto_mode_running:
            tournament_list = list(tournaments.values())
            
            if tournament_list:
                # Display current tournament
                current_tournament = tournament_list[st.session_state.current_slide % len(tournament_list)]
                
                # Show progress
                progress = (st.session_state.current_slide % len(tournament_list) + 1) / len(tournament_list)
                st.progress(progress, text=f"الدوري {st.session_state.current_slide % len(tournament_list) + 1} من {len(tournament_list)}")
                
                render_tournament_display(current_tournament, full_screen=True)
                
                # Auto-advance
                time.sleep(st.session_state.slideshow_interval)
                st.session_state.current_slide += 1
                st.rerun()
        else:
            st.info("اضغط على 'بدء العرض التلقائي' لبدء العرض التلقائي للدوريات")
            
            # Show preview of tournaments
            st.subheader("الدوريات المتاحة")
            for tournament in tournaments.values():
                st.write(f"{get_sport_icon(tournament.sport_type.value)} {tournament.name} - {len(tournament.teams)} فريق")

def render_add_teams_page():
    """Render add teams page"""
    st.title("👥 أضف فرق")
    
    tab1, tab2, tab3 = st.tabs(["إضافة الفرق", "إدارة الفرق", "إدارة المواجهات"])
    
    with tab1:
        st.subheader("إضافة فريق/لاعب جديد")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tournament_name = st.text_input("اسم الدوري")
            sport_options = [sport.value for sport in SportType]
            selected_sport = st.selectbox("نوع الرياضة", sport_options)
        
        with col2:
            team_name_label = get_team_name_label(selected_sport)
            team_name = st.text_input(team_name_label)
            notes = st.text_area("ملاحظات (اختياري)")
        
        if st.button("إنشاء الدوري وإضافة الفريق", type="primary"):
            if tournament_name.strip() and team_name.strip():
                sport_type = SportType(selected_sport)
                
                # Create tournament if it doesn't exist
                tournament_created = tm.create_tournament(tournament_name.strip(), sport_type)
                
                if tournament_created:
                    # Find the created tournament
                    tournaments = tm.get_all_tournaments()
                    created_tournament = None
                    for t in tournaments.values():
                        if t.name == tournament_name.strip() and t.sport_type == sport_type:
                            created_tournament = t
                            break
                    
                    if created_tournament and tm.add_team_to_tournament(created_tournament.id, team_name.strip()):
                        st.success(f"تم إنشاء الدوري '{tournament_name}' وإضافة '{team_name}' بنجاح!")
                        st.rerun()
                    else:
                        st.error("فشل في إضافة الفريق")
                else:
                    st.error("فشل في إنشاء الدوري")
            else:
                st.error("يرجى إدخال اسم الدوري واسم الفريق")
    
    with tab2:
        st.subheader("إدارة الفرق الموجودة")
        
        tournaments = tm.get_all_tournaments()
        
        if tournaments:
            tournament_options = {f"{get_sport_icon(t.sport_type.value)} {t.name}": t.id for t in tournaments.values()}
            selected_tournament_label = st.selectbox("اختر الدوري", list(tournament_options.keys()), key="manage_tournament")
            
            if selected_tournament_label:
                selected_tournament_id = tournament_options[selected_tournament_label]
                tournament = tournaments[selected_tournament_id]
                
                st.write(f"**الدوري:** {tournament.name}")
                st.write(f"**النوع:** {tournament.sport_type.value}")
                
                # Add more teams to existing tournament
                with st.expander("إضافة فريق جديد لهذا الدوري"):
                    team_name_label = get_team_name_label(tournament.sport_type.value)
                    new_team_name = st.text_input(team_name_label, key="new_team_existing")
                    
                    if st.button("إضافة الفريق", type="primary", key="add_to_existing"):
                        if new_team_name.strip():
                            if tm.add_team_to_tournament(selected_tournament_id, new_team_name.strip()):
                                st.success("تم إضافة الفريق بنجاح!")
                                st.rerun()
                            else:
                                st.error("فشل في إضافة الفريق")
                        else:
                            st.error("يرجى إدخال اسم الفريق")
                
                # Display and manage existing teams
                if tournament.teams:
                    st.subheader("الفرق المسجلة")
                    
                    for team_id, team in tournament.teams.items():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**{team.name}**")
                        
                        with col2:
                            if st.button("حذف", key=f"delete_team_{team_id}", type="secondary"):
                                if tm.remove_team_from_tournament(selected_tournament_id, team_id):
                                    st.success("تم حذف الفريق بنجاح!")
                                    st.rerun()
                
                # Tournament management
                if len(tournament.teams) >= 3:
                    with st.expander("إدارة المجموعات والمباريات"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            teams_per_group = st.selectbox("عدد الفرق في كل مجموعة", [3, 4], index=1, key="teams_per_group")
                        
                        with col2:
                            if st.button("إنشاء المجموعات", type="primary", key="create_groups"):
                                if tm.create_groups_for_tournament(selected_tournament_id, teams_per_group):
                                    st.success("تم إنشاء المجموعات بنجاح!")
                                    st.rerun()
                
                # Navigate to detailed management
                if tournament.matches or tournament.knockout_matches:
                    if st.button("إدارة المباريات التفصيلية", type="secondary"):
                        st.session_state.current_tournament = selected_tournament_id
                        st.session_state.page = "match_management"
                        st.rerun()
        else:
            st.info("لا توجد دوريات. قم بإنشاء دوري جديد أولاً.")
    
    with tab3:
        st.subheader("إدارة المواجهات")
        
        tournaments = tm.get_all_tournaments()
        
        if tournaments:
            tournament_options = {f"{get_sport_icon(t.sport_type.value)} {t.name}": t.id for t in tournaments.values()}
            selected_tournament_label = st.selectbox("اختر الدوري", list(tournament_options.keys()), key="match_tournament")
            
            if selected_tournament_label:
                selected_tournament_id = tournament_options[selected_tournament_label]
                tournament = tournaments[selected_tournament_id]
                
                if len(tournament.teams) >= 2:
                    # Show current matches
                    if tournament.matches:
                        st.subheader("مباريات دور المجموعات")
                        
                        for group_id, group in tournament.groups.items():
                            with st.expander(f"{group.name}"):
                                group_matches = [m for m in tournament.matches.values() if m.group_id == group_id]
                                
                                for match in group_matches:
                                    team1 = tournament.teams.get(match.team1_id)
                                    team2 = tournament.teams.get(match.team2_id)
                                    team1_name = team1.name if team1 else 'فريق غير معروف'
                                    team2_name = team2.name if team2 else 'فريق غير معروف'
                                    
                                    if match.is_completed:
                                        winner = match.get_winner()
                                        if winner == match.team1_id:
                                            st.write(f"✅ {team1_name} فاز على {team2_name}")
                                        elif winner == match.team2_id:
                                            st.write(f"✅ {team2_name} فاز على {team1_name}")
                                        else:
                                            st.write(f"🤝 {team1_name} تعادل مع {team2_name}")
                                    else:
                                        st.write(f"⏳ {team1_name} ضد {team2_name} (لم تلعب بعد)")
                    
                    # Knockout stage
                    if tournament.can_generate_knockout():
                        if not tournament.knockout_matches:
                            if st.button("إنشاء دور الإقصاء", type="primary"):
                                if tm.generate_knockout_for_tournament(selected_tournament_id):
                                    st.success("تم إنشاء دور الإقصاء بنجاح!")
                                    st.rerun()
                        else:
                            st.subheader("مباريات دور الإقصاء")
                            
                            rounds = {}
                            for match in tournament.knockout_matches.values():
                                if match.round_type not in rounds:
                                    rounds[match.round_type] = []
                                rounds[match.round_type].append(match)
                            
                            for round_type in ["semi", "final"]:
                                if round_type in rounds:
                                    st.write(f"**{get_round_name(round_type)}**")
                                    
                                    for match in rounds[round_type]:
                                        team1 = tournament.teams.get(match.team1_id)
                                        team2 = tournament.teams.get(match.team2_id)
                                        team1_name = team1.name if team1 else 'فريق غير معروف'
                                        team2_name = team2.name if team2 else 'فريق غير معروف'
                                        
                                        if match.is_completed:
                                            winner = match.get_winner()
                                            if winner:
                                                winner_team = tournament.teams.get(winner)
                                                winner_name = winner_team.name if winner_team else 'فريق غير معروف'
                                                st.write(f"🏆 {winner_name} فاز في مباراة {team1_name} ضد {team2_name}")
                                            else:
                                                st.write(f"🤝 {team1_name} تعادل مع {team2_name}")
                                        else:
                                            st.write(f"⏳ {team1_name} ضد {team2_name} (لم تلعب بعد)")
                else:
                    st.info("يجب إضافة فريقين على الأقل لإنشاء المواجهات")
        else:
            st.info("لا توجد دوريات متاحة")

def render_edit_mode_page():
    """Render edit mode page"""
    st.title("⚙️ تعديل")
    
    st.subheader("إدارة شاملة للنظام")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏆 إدارة الدوريات", width="stretch", type="primary"):
            st.session_state.page = "tournament_management"
            st.rerun()
        
        st.markdown("إدارة الدوريات، إنشاء دوريات جديدة، حذف الدوريات الموجودة")
    
    with col2:
        if st.button("⚙️ الإعدادات المتقدمة", width="stretch", type="secondary"):
            st.info("قريباً - إعدادات متقدمة للنظام")
    
    st.markdown("---")
    
    # Quick access to tournament management
    tournaments = tm.get_all_tournaments()
    
    if tournaments:
        st.subheader("الوصول السريع للدوريات")
        
        for tournament_id, tournament in tournaments.items():
            with st.expander(f"{get_sport_icon(tournament.sport_type.value)} {tournament.name}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("إدارة الفرق", key=f"edit_teams_{tournament_id}", type="primary"):
                        st.session_state.current_tournament = tournament_id
                        st.session_state.page = "team_management"
                        st.rerun()
                
                with col2:
                    if st.button("إدارة المباريات", key=f"edit_matches_{tournament_id}", type="primary"):
                        st.session_state.current_tournament = tournament_id
                        st.session_state.page = "match_management"
                        st.rerun()
                
                with col3:
                    if st.button("حذف الدوري", key=f"delete_tournament_{tournament_id}", type="secondary"):
                        if tm.delete_tournament(tournament_id):
                            st.success("تم حذف الدوري بنجاح!")
                            st.rerun()
                        else:
                            st.error("فشل في حذف الدوري")
    else:
        st.info("لا توجد دوريات للتعديل")

def render_tournament_display(tournament, full_screen=False):
    """Render complete tournament display with tree-like bracket view"""
    # Header with full screen option
    if not full_screen:
        st.header(f"{get_sport_icon(tournament.sport_type.value)} {tournament.name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("عدد الفرق", len(tournament.teams))
            st.metric("عدد المجموعات", len(tournament.groups))
        
        with col2:
            completed_matches = sum(1 for m in tournament.matches.values() if m.is_completed)
            st.metric("المباريات المكتملة", f"{completed_matches}/{len(tournament.matches)}")
            knockout_completed = sum(1 for m in tournament.knockout_matches.values() if m.is_completed)
            st.metric("مباريات الإقصاء المكتملة", f"{knockout_completed}/{len(tournament.knockout_matches)}")
    else:
        # Full screen mode - larger header
        st.markdown(f"<h1 style='text-align: center; font-size: 3rem; margin-bottom: 2rem;'>{get_sport_icon(tournament.sport_type.value)} {tournament.name}</h1>", unsafe_allow_html=True)
    
    # Tournament bracket tree display
    st.markdown("---")
    
    # Group stage section
    if tournament.groups:
        st.markdown(f"<h2 style='text-align: center; color: #1f4e79; margin-bottom: 1.5rem;'>🏁 دور المجموعات</h2>", unsafe_allow_html=True)
        
        # Display groups in columns
        group_cols = st.columns(len(tournament.groups))
        group_winners = []
        
        for i, (group_id, group) in enumerate(tournament.groups.items()):
            with group_cols[i]:
                st.markdown(f"<h4 style='text-align: center; background: linear-gradient(90deg, #1f4e79, #4a90e2); color: white; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>{group.name}</h4>", unsafe_allow_html=True)
                
                # Group standings
                standings = tournament.get_group_standings(group_id)
                
                if standings:
                    # Display top teams prominently
                    for j, team_data in enumerate(standings[:4]):  # Show top 4
                        position_emoji = ["🥇", "🥈", "🥉", "4️⃣"][j] if j < 4 else f"{j+1}️⃣"
                        
                        if j == 0:  # Winner
                            st.markdown(f"<div style='background: gold; color: black; padding: 0.5rem; border-radius: 0.3rem; margin-bottom: 0.3rem; text-align: center; font-weight: bold;'>{position_emoji} {team_data['team_name']}<br>النقاط: {team_data['points']}</div>", unsafe_allow_html=True)
                            group_winners.append(team_data['team_id'])
                        elif j == 1:  # Runner-up
                            st.markdown(f"<div style='background: silver; color: black; padding: 0.5rem; border-radius: 0.3rem; margin-bottom: 0.3rem; text-align: center;'>{position_emoji} {team_data['team_name']}<br>النقاط: {team_data['points']}</div>", unsafe_allow_html=True)
                        elif j == 2:  # Third place
                            st.markdown(f"<div style='background: #cd7f32; color: white; padding: 0.5rem; border-radius: 0.3rem; margin-bottom: 0.3rem; text-align: center;'>{position_emoji} {team_data['team_name']}<br>النقاط: {team_data['points']}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='background: #f0f0f0; color: black; padding: 0.5rem; border-radius: 0.3rem; margin-bottom: 0.3rem; text-align: center;'>{position_emoji} {team_data['team_name']}<br>النقاط: {team_data['points']}</div>", unsafe_allow_html=True)
                
                # Group matches summary
                group_matches = [m for m in tournament.matches.values() if m.group_id == group_id]
                if group_matches:
                    completed_count = sum(1 for m in group_matches if m.is_completed)
                    st.markdown(f"<p style='text-align: center; font-size: 0.9rem; color: #666;'>المباريات: {completed_count}/{len(group_matches)}</p>", unsafe_allow_html=True)
    
    # Knockout stage tree display
    if tournament.knockout_matches:
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; color: #dc3545; margin: 2rem 0;'>🏆 دور الإقصاء</h2>", unsafe_allow_html=True)
        
        # Group knockout matches by round
        rounds = {}
        for match in tournament.knockout_matches.values():
            if match.round_type not in rounds:
                rounds[match.round_type] = []
            rounds[match.round_type].append(match)
        
        # Display knockout tree
        if "semi" in rounds and "final" in rounds:
            # Full knockout tree (Semi + Final)
            col1, col2, col3 = st.columns([2, 1, 2])
            
            # Semi-finals
            with col1:
                st.markdown(f"<h4 style='text-align: center; color: #dc3545;'>نصف النهائي</h4>", unsafe_allow_html=True)
                semi_winners = []
                
                for match in rounds["semi"]:
                    team1 = tournament.teams.get(match.team1_id)
                    team2 = tournament.teams.get(match.team2_id)
                    team1_name = team1.name if team1 else 'فريق غير معروف'
                    team2_name = team2.name if team2 else 'فريق غير معروف'
                    
                    if match.is_completed:
                        winner = match.get_winner()
                        if winner:
                            winner_team = tournament.teams.get(winner)
                            winner_name = winner_team.name if winner_team else 'فريق غير معروف'
                            semi_winners.append(winner)
                            
                            st.markdown(f"""
                            <div style='border: 2px solid #dc3545; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; background: #fff5f5;'>
                                <div style='text-align: center; font-weight: bold; color: #dc3545; margin-bottom: 0.5rem;'>{team1_name} ضد {team2_name}</div>
                                <div style='text-align: center; font-size: 1.2rem;'>{match.team1_score} - {match.team2_score}</div>
                                <div style='text-align: center; background: #dc3545; color: white; padding: 0.3rem; border-radius: 0.3rem; margin-top: 0.5rem;'>🏆 الفائز: {winner_name}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='border: 2px solid #ffc107; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; background: #fffbf0;'>
                                <div style='text-align: center; font-weight: bold; color: #ffc107; margin-bottom: 0.5rem;'>{team1_name} ضد {team2_name}</div>
                                <div style='text-align: center; font-size: 1.2rem;'>{match.team1_score} - {match.team2_score}</div>
                                <div style='text-align: center; background: #ffc107; color: black; padding: 0.3rem; border-radius: 0.3rem; margin-top: 0.5rem;'>🤝 تعادل</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='border: 2px dashed #6c757d; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; background: #f8f9fa;'>
                            <div style='text-align: center; color: #6c757d;'>{team1_name} ضد {team2_name}</div>
                            <div style='text-align: center; color: #6c757d; margin-top: 0.5rem;'>⏳ لم تلعب بعد</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Arrow or connector
            with col2:
                st.markdown("<div style='text-align: center; font-size: 3rem; margin-top: 3rem;'>➡️</div>", unsafe_allow_html=True)
            
            # Final
            with col3:
                st.markdown(f"<h4 style='text-align: center; color: #dc3545;'>النهائي</h4>", unsafe_allow_html=True)
                
                for match in rounds["final"]:
                    team1 = tournament.teams.get(match.team1_id)
                    team2 = tournament.teams.get(match.team2_id)
                    team1_name = team1.name if team1 else 'فريق غير معروف'
                    team2_name = team2.name if team2 else 'فريق غير معروف'
                    
                    if match.is_completed:
                        winner = match.get_winner()
                        if winner:
                            winner_team = tournament.teams.get(winner)
                            winner_name = winner_team.name if winner_team else 'فريق غير معروف'
                            
                            st.markdown(f"""
                            <div style='border: 3px solid #ffd700; border-radius: 0.5rem; padding: 1.5rem; background: linear-gradient(45deg, #ffd700, #ffed4e);'>
                                <div style='text-align: center; font-weight: bold; font-size: 1.2rem; margin-bottom: 0.5rem;'>{team1_name} ضد {team2_name}</div>
                                <div style='text-align: center; font-size: 1.5rem; font-weight: bold;'>{match.team1_score} - {match.team2_score}</div>
                                <div style='text-align: center; background: #dc3545; color: white; padding: 0.5rem; border-radius: 0.3rem; margin-top: 0.5rem; font-size: 1.1rem;'>👑 البطل: {winner_name}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='border: 3px solid #ffc107; border-radius: 0.5rem; padding: 1.5rem; background: linear-gradient(45deg, #ffc107, #ffed4e);'>
                                <div style='text-align: center; font-weight: bold; font-size: 1.2rem; margin-bottom: 0.5rem;'>{team1_name} ضد {team2_name}</div>
                                <div style='text-align: center; font-size: 1.5rem; font-weight: bold;'>{match.team1_score} - {match.team2_score}</div>
                                <div style='text-align: center; background: #ffc107; color: black; padding: 0.5rem; border-radius: 0.3rem; margin-top: 0.5rem; font-size: 1.1rem;'>🤝 تعادل في النهائي</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='border: 3px dashed #6c757d; border-radius: 0.5rem; padding: 1.5rem; background: #f8f9fa;'>
                            <div style='text-align: center; color: #6c757d; font-size: 1.2rem;'>{team1_name} ضد {team2_name}</div>
                            <div style='text-align: center; color: #6c757d; margin-top: 0.5rem; font-size: 1.1rem;'>⏳ النهائي لم يلعب بعد</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        elif "final" in rounds:
            # Direct final
            st.markdown(f"<h4 style='text-align: center; color: #dc3545;'>النهائي</h4>", unsafe_allow_html=True)
            
            for match in rounds["final"]:
                team1 = tournament.teams.get(match.team1_id)
                team2 = tournament.teams.get(match.team2_id)
                team1_name = team1.name if team1 else 'فريق غير معروف'
                team2_name = team2.name if team2 else 'فريق غير معروف'
                
                if match.is_completed:
                    winner = match.get_winner()
                    if winner:
                        winner_team = tournament.teams.get(winner)
                        winner_name = winner_team.name if winner_team else 'فريق غير معروف'
                        
                        st.markdown(f"""
                        <div style='border: 3px solid #ffd700; border-radius: 0.5rem; padding: 2rem; background: linear-gradient(45deg, #ffd700, #ffed4e); text-align: center;'>
                            <div style='font-weight: bold; font-size: 1.5rem; margin-bottom: 1rem;'>{team1_name} ضد {team2_name}</div>
                            <div style='font-size: 2rem; font-weight: bold; margin-bottom: 1rem;'>{match.team1_score} - {match.team2_score}</div>
                            <div style='background: #dc3545; color: white; padding: 1rem; border-radius: 0.5rem; font-size: 1.3rem;'>👑 البطل: {winner_name}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='border: 3px dashed #6c757d; border-radius: 0.5rem; padding: 2rem; background: #f8f9fa; text-align: center;'>
                        <div style='color: #6c757d; font-size: 1.5rem;'>{team1_name} ضد {team2_name}</div>
                        <div style='color: #6c757d; margin-top: 1rem; font-size: 1.2rem;'>⏳ النهائي لم يلعب بعد</div>
                    </div>
                    """, unsafe_allow_html=True)

def render_dashboard():
    """Render main dashboard"""
    # Header section
    st.markdown("<h1 style='text-align: center; color: #1f4e79;'>🏆 نادي الأمين</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 2rem;'>أهلاً بكم</h3>", unsafe_allow_html=True)
    
    # Main buttons section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 أضف نتائج", key="add_results", width="stretch", type="primary"):
            st.session_state.page = "add_results"
            st.rerun()
    
    with col2:
        if st.button("📺 عرض نتائج", key="view_results", width="stretch", type="primary"):
            st.session_state.page = "view_results"
            st.rerun()
    
    with col3:
        if st.button("👥 أضف فرق", key="add_teams", width="stretch", type="primary"):
            st.session_state.page = "add_teams"
            st.rerun()
    
    # Edit button
    st.markdown("---")
    col_edit = st.columns([1, 2, 1])
    with col_edit[1]:
        if st.button("⚙️ تعديل", key="edit_main", width="stretch", type="secondary"):
            st.session_state.page = "edit_mode"
            st.rerun()
    
    # Show quick stats if tournaments exist
    tournaments = tm.get_all_tournaments()
    if tournaments:
        st.markdown("---")
        st.subheader("نظرة سريعة")
        
        # Quick statistics
        total_teams = sum(len(t.teams) for t in tournaments.values())
        total_matches = sum(len(t.matches) + len(t.knockout_matches) for t in tournaments.values())
        completed_matches = sum(sum(1 for m in t.matches.values() if m.is_completed) + 
                              sum(1 for m in t.knockout_matches.values() if m.is_completed) 
                              for t in tournaments.values())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("عدد الدوريات", len(tournaments))
        with col2:
            st.metric("إجمالي الفرق", total_teams)
        with col3:
            st.metric("المباريات المكتملة", f"{completed_matches}/{total_matches}")
        
        # Tournament previews
        st.subheader("الدوريات النشطة")
        for tournament in tournaments.values():
            with st.expander(f"{get_sport_icon(tournament.sport_type.value)} {tournament.name}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**النوع:** {tournament.sport_type.value}")
                    st.write(f"**عدد الفرق:** {len(tournament.teams)}")
                with col2:
                    group_matches_completed = sum(1 for m in tournament.matches.values() if m.is_completed)
                    knockout_matches_completed = sum(1 for m in tournament.knockout_matches.values() if m.is_completed)
                    st.write(f"**مباريات المجموعات:** {group_matches_completed}/{len(tournament.matches)}")
                    st.write(f"**مباريات الإقصاء:** {knockout_matches_completed}/{len(tournament.knockout_matches)}")
    else:
        st.markdown("---")
        st.info("مرحباً بك في نادي الأمين! ابدأ بإضافة فرق جديدة لإنشاء دورياتك الأولى.")

def main():
    """Main application function"""
    # Add back to home button on all non-dashboard pages
    if st.session_state.page != "dashboard":
        if st.button("🏠 العودة للرئيسية", type="secondary"):
            st.session_state.page = "dashboard"
            if 'current_tournament' in st.session_state:
                del st.session_state.current_tournament
            st.rerun()
        st.markdown("---")
    
    # Route to appropriate page
    if st.session_state.page == "dashboard":
        render_dashboard()
    
    elif st.session_state.page == "add_results":
        render_add_results_page()
    
    elif st.session_state.page == "view_results":
        render_view_results_page()
    
    elif st.session_state.page == "add_teams":
        render_add_teams_page()
    
    elif st.session_state.page == "edit_mode":
        render_edit_mode_page()
    
    # Legacy pages for backward compatibility
    elif st.session_state.page == "tournament_management":
        tm.render_tournament_management()
    
    elif st.session_state.page == "team_management":
        if 'current_tournament' in st.session_state:
            tm.render_team_management(st.session_state.current_tournament)
        else:
            st.error("لم يتم تحديد الدوري")
            st.session_state.page = "dashboard"
            st.rerun()
    
    elif st.session_state.page == "match_management":
        if 'current_tournament' in st.session_state:
            tm.render_match_management(st.session_state.current_tournament)
        else:
            st.error("لم يتم تحديد الدوري")
            st.session_state.page = "dashboard"
            st.rerun()

if __name__ == "__main__":
    main()
