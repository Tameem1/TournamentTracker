import streamlit as st
import time
from tournament_manager import TournamentManager
from utils import get_sport_icon, get_round_name
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

def render_sidebar():
    """Render sidebar navigation"""
    st.sidebar.title("🏆 نادي الأمين")
    st.sidebar.markdown("---")
    
    # Navigation menu
    menu_options = {
        "📺 الصفحة الرئيسية": "dashboard",
        "⚙️ إدارة الدوريات": "tournament_management",
    }
    
    for label, page in menu_options.items():
        if st.sidebar.button(label, use_container_width=True):
            st.session_state.page = page
            if 'current_tournament' in st.session_state:
                del st.session_state.current_tournament
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Viewing mode selection (only show on dashboard)
    if st.session_state.page == "dashboard":
        st.sidebar.subheader("طريقة العرض")
        
        viewing_mode = st.sidebar.radio(
            "اختر طريقة العرض",
            ["manual", "automatic"],
            format_func=lambda x: "يدوي" if x == "manual" else "تلقائي",
            index=0 if st.session_state.viewing_mode == "manual" else 1
        )
        
        if viewing_mode != st.session_state.viewing_mode:
            st.session_state.viewing_mode = viewing_mode
            st.session_state.auto_mode_running = False
            st.rerun()
        
        # Automatic mode settings
        if viewing_mode == "automatic":
            interval = st.sidebar.slider(
                "مدة العرض (ثواني)",
                min_value=5,
                max_value=60,
                value=st.session_state.slideshow_interval,
                step=5
            )
            st.session_state.slideshow_interval = interval
            
            if st.sidebar.button("بدء العرض التلقائي", type="primary"):
                st.session_state.auto_mode_running = True
                st.rerun()
            
            if st.sidebar.button("إيقاف العرض التلقائي", type="secondary"):
                st.session_state.auto_mode_running = False
                st.rerun()

def render_tournament_display(tournament):
    """Render complete tournament display with groups and knockout stages"""
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
    
    # Group stage display
    if tournament.groups:
        st.subheader("دور المجموعات")
        
        for group_id, group in tournament.groups.items():
            with st.expander(f"{group.name}", expanded=True):
                # Group standings
                standings = tournament.get_group_standings(group_id)
                
                if standings:
                    st.write("**الترتيب:**")
                    
                    # Create standings table
                    standings_data = []
                    for i, team_data in enumerate(standings):
                        standings_data.append({
                            "المركز": i + 1,
                            "الفريق": team_data['team_name'],
                            "لعب": team_data['played'],
                            "فاز": team_data['won'],
                            "تعادل": team_data['drawn'],
                            "خسر": team_data['lost'],
                            "النقاط": team_data['points'],
                            "فارق الأهداف": team_data['goal_difference']
                        })
                    
                    st.dataframe(standings_data, use_container_width=True)
                
                # Group matches
                group_matches = [m for m in tournament.matches.values() if m.group_id == group_id]
                if group_matches:
                    st.write("**المباريات:**")
                    
                    for match in group_matches:
                        team1_name = tournament.teams.get(match.team1_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
                        team2_name = tournament.teams.get(match.team2_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
                        
                        if match.is_completed:
                            st.write(f"✅ {team1_name} {match.team1_score} - {match.team2_score} {team2_name}")
                        else:
                            st.write(f"⏳ {team1_name} vs {team2_name} (لم تلعب بعد)")
    
    # Knockout stage display
    if tournament.knockout_matches:
        st.subheader("دور الإقصاء")
        
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
                    team1_name = tournament.teams.get(match.team1_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
                    team2_name = tournament.teams.get(match.team2_id, type('obj', (object,), {'name': 'فريق غير معروف'})).name
                    
                    if match.is_completed:
                        winner = match.get_winner()
                        if winner:
                            winner_name = tournament.teams.get(winner, type('obj', (object,), {'name': 'فريق غير معروف'})).name
                            st.write(f"🏆 {team1_name} {match.team1_score} - {match.team2_score} {team2_name} (الفائز: {winner_name})")
                        else:
                            st.write(f"🤝 {team1_name} {match.team1_score} - {match.team2_score} {team2_name} (تعادل)")
                    else:
                        st.write(f"⏳ {team1_name} vs {team2_name} (لم تلعب بعد)")

def render_dashboard():
    """Render main dashboard"""
    st.title("🏆 دوريات نادي الأمين")
    
    tournaments = tm.get_all_tournaments()
    
    if not tournaments:
        st.info("لا توجد دوريات حالياً. قم بإنشاء دوري جديد من قائمة إدارة الدوريات.")
        return
    
    if st.session_state.viewing_mode == "manual":
        # Manual viewing mode
        st.subheader("اختر الدوري للعرض")
        
        tournament_options = {f"{get_sport_icon(t.sport_type.value)} {t.name}": t.id for t in tournaments.values()}
        selected_tournament_label = st.selectbox("الدوري", list(tournament_options.keys()))
        
        if selected_tournament_label:
            selected_tournament_id = tournament_options[selected_tournament_label]
            selected_tournament = tournaments[selected_tournament_id]
            
            st.markdown("---")
            render_tournament_display(selected_tournament)
    
    else:
        # Automatic viewing mode
        if st.session_state.auto_mode_running:
            tournament_list = list(tournaments.values())
            
            if tournament_list:
                # Display current tournament
                current_tournament = tournament_list[st.session_state.current_slide % len(tournament_list)]
                
                # Show progress
                progress = (st.session_state.current_slide % len(tournament_list) + 1) / len(tournament_list)
                st.progress(progress, text=f"الدوري {st.session_state.current_slide % len(tournament_list) + 1} من {len(tournament_list)}")
                
                render_tournament_display(current_tournament)
                
                # Auto-advance
                time.sleep(st.session_state.slideshow_interval)
                st.session_state.current_slide += 1
                st.rerun()
        else:
            st.info("اضغط على 'بدء العرض التلقائي' في القائمة الجانبية لبدء العرض التلقائي للدوريات")
            
            # Show preview of tournaments
            st.subheader("الدوريات المتاحة")
            for tournament in tournaments.values():
                st.write(f"{get_sport_icon(tournament.sport_type.value)} {tournament.name} - {len(tournament.teams)} فريق")

def main():
    """Main application function"""
    render_sidebar()
    
    # Route to appropriate page
    if st.session_state.page == "dashboard":
        render_dashboard()
    
    elif st.session_state.page == "tournament_management":
        tm.render_tournament_management()
    
    elif st.session_state.page == "team_management":
        if 'current_tournament' in st.session_state:
            tm.render_team_management(st.session_state.current_tournament)
        else:
            st.error("لم يتم تحديد الدوري")
            st.session_state.page = "tournament_management"
            st.rerun()
    
    elif st.session_state.page == "match_management":
        if 'current_tournament' in st.session_state:
            tm.render_match_management(st.session_state.current_tournament)
        else:
            st.error("لم يتم تحديد الدوري")
            st.session_state.page = "tournament_management"
            st.rerun()

if __name__ == "__main__":
    main()
