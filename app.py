import streamlit as st
import streamlit.components.v1 as components
import time
import random
import urllib.parse
from tournament_manager import TournamentManager
from utils import get_sport_icon, get_round_name, get_team_name_label
from models import SportType

# Configure page
st.set_page_config(
    page_title="دوريات نادي الأمين",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="auto"
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
if 'auto_slides_seed' not in st.session_state:
    st.session_state.auto_slides_seed = 0

# ---------- Global styling & sidebar ----------
def match_completed(m):
    try:
        status_val = m.status
        # Handle Enum or raw string
        is_done = (str(getattr(status_val, 'value', status_val)) == "مكتملة")
        return is_done and m.team1_score is not None and m.team2_score is not None
    except Exception:
        return False

def inject_global_styles():
    st.markdown(
        """
        <style>
        :root {
            --brand-primary: #1f4e79;
            --brand-primary-700: #153956;
            --surface: #ffffff;
            --surface-muted: #f8fafc;
            --border: #e5e7eb;
            --text: #111111;
            --text-strong: #0f172a;
        }
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
        html, body, [class*="css"] {
            direction: rtl;
            font-family: 'Cairo', -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, "Apple Color Emoji", "Noto Color Emoji", sans-serif;
        }
        /* Core brand overrides */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--text-strong); }
        div.stButton>button[kind="primary"], div.stButton>button[data-baseweb="button"] {
            background: var(--brand-primary) !important;
            border-color: var(--brand-primary) !important;
            color: #ffffff !important;
        }
        div.stButton>button[kind="secondary"] {
            border-color: var(--brand-primary) !important;
            color: var(--brand-primary) !important;
        }
        div.stButton>button { border-radius: 10px !important; }
        /* Buttons */
        button[kind="primary"], button[data-baseweb="button"] { border-radius: 10px !important; }
        /* Cards */
        .ux-card { 
            border-radius: 12px; 
            padding: 1rem; 
            background: var(--surface); 
            border: 1px solid var(--border); 
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            color: var(--text);
        }
        .ux-card-accent {
            background: linear-gradient(180deg, var(--surface-muted), var(--surface));
        }
        .ux-card, .ux-card * { color: var(--text) !important; }
        .ux-card:hover { box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-color: var(--border); }
        .ux-muted { color: #6c757d; }
        .ux-section-title { color: var(--brand-primary); margin: 0.5rem 0 1rem 0; }
        .chip { display:inline-block; padding: 2px 8px; border-radius:999px; background:#eef2f7; color:var(--text); font-size:12px; border:1px solid var(--border); }
        .chip-accent { background: rgba(31,78,121,0.08); color: var(--brand-primary); border-color: rgba(31,78,121,0.25); }
        .chip-green { background:#e9fbe7; border-color:#b7f0b0; color:#0a5c2b; }
        .chip-amber { background:#fff8e1; border-color:#ffe08a; color:#7a5200; }
        /* Professional tables */
        .pro-table { width:100%; border-collapse:separate; border-spacing:0; background:var(--surface); border:1px solid var(--border); border-radius:12px; overflow:hidden; }
        .pro-table th, .pro-table td { padding:10px 12px; border-bottom:1px solid var(--border); text-align:center; color:var(--text); }
        .pro-table th { background:var(--surface-muted); font-weight:800; color:var(--text-strong); }
        .pro-table tbody tr:nth-child(even) { background:#f9fafb; }
        .pro-table tr:hover { background:#f5f7fa; }
        .section-title { text-align:center; color:var(--brand-primary); margin: 1rem 0 0.5rem; font-weight:800; }
        .subsection-title { text-align:center; color:#111111; margin: 0.5rem 0; font-weight:700; }

        /* Inputs & widgets */
        .stTextInput input, .stNumberInput input, .stSelectbox select, .stMultiSelect [role="combobox"], textarea {
            border-radius: 10px !important;
        }
        [data-testid="stMetricValue"] { color: var(--brand-primary) !important; }
        [data-testid="stSidebar"] { background: var(--surface-muted) !important; }
        /* Remove top whitespace globally */
        html, body { margin-top: 0 !important; padding-top: 0 !important; }
        [data-testid="stHeader"], header { display: none !important; height: 0 !important; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stAppViewContainer"] { padding-top: 0 !important; }
        .block-container { padding-top: 0 !important; margin-top: 0 !important; }
        .block-container > :first-child { margin-top: 0 !important; }
        /* Completely remove Streamlit's sidebar UI */
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-right: 0 !important; margin-left: 0 !important; }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .block-container { padding: 0.5rem !important; }
            .stButton > button { font-size: 14px !important; padding: 0.5rem !important; }
            .stSelectbox, .stTextInput, .stNumberInput { font-size: 16px !important; }
            .stColumns > div { padding: 0.25rem !important; }
            .pro-table th, .pro-table td { padding: 6px 4px !important; font-size: 12px !important; }
            .section-title { font-size: 1.1rem !important; margin: 0.5rem 0 !important; }
            .subsection-title { font-size: 1rem !important; margin: 0.25rem 0 !important; }
            .ux-card { padding: 0.75rem !important; margin-bottom: 0.5rem !important; }
            .chip { font-size: 11px !important; padding: 2px 6px !important; }
            .top-nav { padding: 4px 6px !important; }
            .top-nav-row { flex-direction: column !important; gap: 4px !important; }
            .top-stats { margin-right: 0 !important; justify-content: center !important; }
        }
        
        @media (max-width: 480px) {
            .block-container { padding: 0.25rem !important; }
            .stButton > button { font-size: 12px !important; padding: 0.4rem !important; }
            .pro-table th, .pro-table td { padding: 4px 2px !important; font-size: 11px !important; }
            .section-title { font-size: 1rem !important; }
            .subsection-title { font-size: 0.9rem !important; }
            .ux-card { padding: 0.5rem !important; }
            .chip { font-size: 10px !important; padding: 1px 4px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _sport_background_css(sport_name: str) -> str:
    palettes = {
        "كرة قدم": "linear-gradient(135deg, #0f9d58 0%, #0b7a43 100%)",
        "كرة سلة": "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
        "تنس": "linear-gradient(135deg, #84cc16 0%, #65a30d 100%)",
        "بينغ بونغ": "linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%)",
    }
    return palettes.get(sport_name, "linear-gradient(135deg, #1f4e79 0%, #153956 100%)")

def _sport_accent_color(sport_name: str) -> str:
    """Primary accent color per sport for consistent theming."""
    accents = {
        "كرة قدم": "#0f9d58",
        "كرة سلة": "#f97316",
        "تنس": "#84cc16",
        "بينغ بونغ": "#0ea5e9",
    }
    return accents.get(sport_name, "#1f4e79")

def _sport_tile_data_uri(emoji: str) -> str:
    # SVG tile with faint emoji watermark
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'>
      <rect width='120' height='120' fill='none'/>
      <text x='60' y='70' font-size='64' text-anchor='middle' opacity='0.09'>{emoji}</text>
    </svg>
    """.strip()
    encoded = urllib.parse.quote(svg)
    return f"url('data:image/svg+xml;utf8,{encoded}')"

def _sport_scene_tile_data_uri(sport_name: str) -> str:
    # Subtle field/court motifs per sport
    if sport_name == "كرة قدم":
        svg = """
        <svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>
          <rect width='240' height='240' fill='none'/>
          <rect x='10' y='10' width='220' height='220' fill='none' stroke='white' stroke-opacity='0.12' stroke-width='2'/>
          <circle cx='120' cy='120' r='30' fill='none' stroke='white' stroke-opacity='0.12' stroke-width='2'/>
          <line x1='120' y1='10' x2='120' y2='230' stroke='white' stroke-opacity='0.12' stroke-width='2'/>
        </svg>
        """
    elif sport_name == "كرة سلة":
        svg = """
        <svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>
          <rect width='240' height='240' fill='none'/>
          <path d='M0,80 L240,80 M0,160 L240,160' stroke='white' stroke-opacity='0.10' stroke-width='3'/>
          <circle cx='120' cy='120' r='60' fill='none' stroke='white' stroke-opacity='0.08' stroke-width='3'/>
        </svg>
        """
    elif sport_name == "تنس":
        svg = """
        <svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>
          <rect width='240' height='240' fill='none'/>
          <rect x='20' y='20' width='200' height='200' fill='none' stroke='white' stroke-opacity='0.14' stroke-width='2'/>
          <line x1='120' y1='20' x2='120' y2='220' stroke='white' stroke-opacity='0.14' stroke-width='2'/>
          <line x1='20' y1='120' x2='220' y2='120' stroke='white' stroke-opacity='0.14' stroke-width='2'/>
        </svg>
        """
    else:  # بينغ بونغ
        svg = """
        <svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>
          <rect width='240' height='240' fill='none'/>
          <path d='M0,0 L240,240 M240,0 L0,240' stroke='white' stroke-opacity='0.06' stroke-width='2'/>
          <circle cx='60' cy='60' r='12' fill='white' fill-opacity='0.06'/>
          <circle cx='180' cy='180' r='12' fill='white' fill-opacity='0.06'/>
        </svg>
        """
    encoded = urllib.parse.quote(svg.strip())
    return f"url('data:image/svg+xml;utf8,{encoded}')"

def apply_sport_background(sport_name: str, fullscreen: bool = False):
    bg = _sport_background_css(sport_name)
    # Use sport icon as watermarked pattern
    from utils import get_sport_icon
    emoji = get_sport_icon(sport_name)
    tile = _sport_tile_data_uri(emoji)
    scene = _sport_scene_tile_data_uri(sport_name)
    accent = _sport_accent_color(sport_name)
    if fullscreen:
        st.markdown(
            f"""
            <style>
            :root {{ --brand-primary: {accent}; }}
            html, body {{ height:100%; overflow:hidden; }}
            body {{ background-image: {bg}, {scene}, {tile}; background-repeat: no-repeat, repeat, repeat; background-size: cover, 240px 240px, 120px 120px; background-attachment: fixed, fixed, fixed; background-position: center top, left top, left top; }}
            .block-container {{ background: rgba(255,255,255,0.85); border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.10); backdrop-filter: blur(1.5px); }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Embedded mode: keep normal page chrome and scrolling; lighter overlay
        st.markdown(
            f"""
            <style>
            :root {{ --brand-primary: {accent}; }}
            body {{ background-image: {bg}, {scene}, {tile}; background-repeat: no-repeat, repeat, repeat; background-size: cover, 240px 240px, 120px 120px; background-attachment: fixed, fixed, fixed; background-position: center top, left top, left top; }}
            .block-container {{ background: rgba(255,255,255,0.92); border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }}
            </style>
            """,
            unsafe_allow_html=True,
        )

def apply_fullscreen_chrome():
    """Hide sidebar and Streamlit chrome for true fullscreen displays."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stToolbar"], [data-testid="stStatusWidget"] { display: none !important; }
        #MainMenu { visibility: hidden; }
        header { visibility: hidden; }
        footer { visibility: hidden; }
        [data-testid="stDecoration"] { display: none !important; }
        .block-container { padding-top: 0; padding-bottom: 0.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def apply_compact_no_scroll(scale_percent: int = 90):
    """Compact styling to fit all content in one screen without scrolling and hide sidebar."""
    scale = max(50, min(100, int(scale_percent)))
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"], [data-testid="stToolbar"], [data-testid="stStatusWidget"], header, footer, [data-testid="stDecoration"] {{ display: none !important; }}
        html, body {{ overflow: hidden !important; }}
        .block-container {{ padding-top: 0.25rem; padding-bottom: 0.25rem; height: 100vh; overflow: hidden; transform: scale({scale/100}); transform-origin: top center; }}
        .pro-table th, .pro-table td {{ padding: 6px 8px; font-size: 12px; }}
        .section-title {{ margin: 0.25rem 0; font-size: 1rem; }}
        .subsection-title {{ margin: 0.25rem 0; font-size: 0.95rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _build_auto_slides(tournaments_list):
    """Build a linear list of slides: (tournament_id, kind, payload)
    kind: 'overview' | 'groups_chunk' | 'group' | 'knockout'
    payload: None | list[group_id] | 'semi'/'final'
    """
    slides = []
    for t in tournaments_list:
        # Build group chunks to ensure each slide fits
        if t.groups:
            # Estimate rows per group = standings rows + match rows
            group_ids = list(t.groups.keys())
            current_chunk = []
            current_rows = 0
            max_rows = 28  # target rows per slide
            for gid in group_ids:
                try:
                    s_rows = len(t.get_group_standings(gid))
                except Exception:
                    s_rows = len(t.groups[gid].team_ids)
                m_rows = sum(1 for m in t.matches.values() if m.group_id == gid)
                g_rows = max(2, s_rows) + max(1, m_rows) + 2  # include headers/margins
                # If adding this group would overflow the target, flush current chunk
                if current_rows > 0 and current_rows + g_rows > max_rows:
                    slides.append((t.id, 'groups_chunk', current_chunk))
                    current_chunk = []
                    current_rows = 0
                current_chunk.append(gid)
                current_rows += g_rows
            if current_chunk:
                slides.append((t.id, 'groups_chunk', current_chunk))
        # One slide for knockout (if exists)
        if t.knockout_matches:
            slides.append((t.id, 'knockout', None))
    return slides

def _render_auto_slide(tournament, kind, payload):
    """Render a single slide in fullscreen mode."""
    # Common title
    title = f"{get_sport_icon(tournament.sport_type.value)} {tournament.name}"
    st.markdown(
        f"<h1 style='text-align:center;margin:0 0 0.5rem;'>{title}</h1>",
        unsafe_allow_html=True,
    )
    # Slide-specific styles (cards and list rows instead of tables)
    st.markdown(
        """
        <style>
        .slide-card { background: rgba(255,255,255,0.95); border: 1px solid var(--border); border-radius: 12px; padding: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
        .slide-list { display: flex; flex-direction: column; gap: 6px; }
        .slide-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 10px; background: #ffffff; border: 1px solid var(--border); }
        .slide-row .name { font-weight: 700; color: var(--text-strong); }
        .slide-chip { display:inline-block; min-width: 44px; text-align:center; padding: 2px 10px; border-radius: 999px; background: rgba(31,78,121,0.08); color: var(--brand-primary); border: 1px solid rgba(31,78,121,0.25); font-weight: 800; }
        .slide-score { display:inline-block; min-width: 72px; text-align:center; padding: 2px 12px; border-radius: 999px; background: rgba(31,78,121,0.10); color: var(--brand-primary); border: 1px solid rgba(31,78,121,0.25); font-weight: 800; }
        .slide-rows-3 { display:grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items:center; }
        .slide-xs { font-size: 12px; color: #6c757d; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if kind == 'groups_chunk' and tournament.groups:
        st.markdown(f"<div class='section-title'>🏁 دور المجموعات</div>", unsafe_allow_html=True)
        # Grid CSS and compact table styles for slideshow
        st.markdown(
            """
            <style>
            .groups-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
            .group-card { background: rgba(255,255,255,0.96); border: 1px solid var(--border); border-radius: 12px; padding: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
            .group-title { font-weight: 800; margin-bottom: 6px; color: var(--text-strong); text-align: center; }
            .group-card .pro-table.compact th, .group-card .pro-table.compact td { padding: 6px 8px; font-size: 12px; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        group_cards_html = []
        for gid, group in tournament.groups.items():
            # Standings table
            standings = tournament.get_group_standings(gid)
            s_rows_html = "".join([f"<tr><td>{row['team_name']}</td><td>{row['points']}</td></tr>" for row in standings])
            if not s_rows_html:
                s_rows_html = "<tr><td>—</td><td>0</td></tr>"
            s_table_html = (
                "<table class='pro-table compact'>"
                "<thead><tr><th>الفريق</th><th>النقاط</th></tr></thead>"
                f"<tbody>{s_rows_html}</tbody>"
                "</table>"
            )
            # Matches table
            group_matches = [m for m in tournament.matches.values() if m.group_id == gid]
            m_rows_html = "".join([
                f"<tr><td>{(tournament.teams.get(m.team1_id).name if m.team1_id in tournament.teams else '—')}</td><td>{(f'{m.team1_score} - {m.team2_score}' if m.is_completed else '—')}</td><td>{(tournament.teams.get(m.team2_id).name if m.team2_id in tournament.teams else '—')}</td></tr>"
                for m in group_matches
            ])
            if not m_rows_html:
                m_rows_html = "<tr><td>—</td><td>—</td><td>—</td></tr>"
            m_table_html = (
                "<table class='pro-table compact'>"
                "<thead><tr><th>الفريق 1</th><th>النتيجة</th><th>الفريق 2</th></tr></thead>"
                f"<tbody>{m_rows_html}</tbody>"
                "</table>"
            )
            card_html = (
                "<div class='group-card'>"
                f"<div class='group-title'>{group.name}</div>"
                "<div class='slide-xs' style='margin:2px 0 4px 0'>الترتيب</div>"
                f"{s_table_html}"
                "<div class='slide-xs' style='margin:8px 0 4px 0'>المباريات</div>"
                f"{m_table_html}"
                "</div>"
            )
            group_cards_html.append(card_html)
        st.markdown(
            """
            <div class='groups-grid'>
              {cards}
            </div>
            """.replace("{cards}", "\n".join(group_cards_html)),
            unsafe_allow_html=True,
        )
    elif kind == 'group' and payload in tournament.groups:
        group = tournament.groups[payload]
        st.markdown(f"<div class='section-title'>🏁 {group.name}</div>", unsafe_allow_html=True)
        standings = tournament.get_group_standings(group.id)
        # Standings list (no tables)
        s_rows = [
            f"<div class='slide-row'><div class='name'>{row['team_name']}</div><div class='slide-chip'>{row['points']}</div></div>"
            for row in standings
        ]
        st.markdown("""
            <div class='slide-card'>
              <div class='slide-list'>
                {rows}
              </div>
            </div>
        """.replace("{rows}", "\n".join(s_rows)), unsafe_allow_html=True)
        # Matches table
        group_matches = [m for m in tournament.matches.values() if m.group_id == group.id]
        st.markdown(f"<div class='subsection-title'>نتائج المباريات</div>", unsafe_allow_html=True)
        if group_matches:
            m_rows = []
            for m in group_matches:
                t1 = tournament.teams.get(m.team1_id)
                t2 = tournament.teams.get(m.team2_id)
                n1 = t1.name if t1 else '—'
                n2 = t2.name if t2 else '—'
                score = f"{m.team1_score} - {m.team2_score}" if m.is_completed else "—"
                m_rows.append(
                    f"<div class='slide-row'><div class='name'>{n1}</div><div class='slide-score'>{score}</div><div class='name'>{n2}</div></div>"
                )
            st.markdown("""
                <div class='slide-card'>
                  <div class='slide-list'>
                    {rows}
                  </div>
                </div>
            """.replace("{rows}", "\n".join(m_rows)), unsafe_allow_html=True)
        else:
            st.info("لا توجد مباريات في هذه المجموعة")
    elif kind == 'knockout':
        st.markdown(f"<div class='section-title'>🏆 دور الإقصاء</div>", unsafe_allow_html=True)
        rounds = {}
        for match in tournament.knockout_matches.values():
            rounds.setdefault(match.round_type, []).append(match)
        for round_type in ["semi", "final"]:
            if round_type in rounds:
                st.markdown(f"<div class='subsection-title'>{get_round_name(round_type)}</div>", unsafe_allow_html=True)
                k_rows = []
                for match in rounds[round_type]:
                    team1 = tournament.teams.get(match.team1_id)
                    team2 = tournament.teams.get(match.team2_id)
                    team1_name = team1.name if team1 else '—'
                    team2_name = team2.name if team2 else '—'
                    score = f"{match.team1_score} - {match.team2_score}" if match.is_completed else "—"
                    k_rows.append(
                        f"<div class='slide-row'><div class='name'>{team1_name}</div><div class='slide-score'>{score}</div><div class='name'>{team2_name}</div></div>"
                    )
                st.markdown("""
                    <div class='slide-card'>
                      <div class='slide-list'>
                        {rows}
                      </div>
                    </div>
                """.replace("{rows}", "\n".join(k_rows)), unsafe_allow_html=True)
    else:
        st.info("لا توجد بيانات للعرض")

def _compute_overall_standings(tournament):
    stats = {}
    # init teams
    for team_id, team in tournament.teams.items():
        stats[team_id] = {
            'team_id': team_id,
            'team_name': team.name,
            'played': 0,
            'won': 0,
            'drawn': 0,
            'lost': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_difference': 0,
            'points': 0,
        }
    # accumulate from completed group matches
    for match in tournament.matches.values():
        if not match.is_completed:
            continue
        t1 = stats.get(match.team1_id)
        t2 = stats.get(match.team2_id)
        if not t1 or not t2:
            continue
        t1['played'] += 1
        t2['played'] += 1
        t1['goals_for'] += match.team1_score
        t1['goals_against'] += match.team2_score
        t2['goals_for'] += match.team2_score
        t2['goals_against'] += match.team1_score
        if match.team1_score > match.team2_score:
            t1['won'] += 1
            t1['points'] += 3
            t2['lost'] += 1
        elif match.team2_score > match.team1_score:
            t2['won'] += 1
            t2['points'] += 3
            t1['lost'] += 1
        else:
            t1['drawn'] += 1
            t2['drawn'] += 1
            t1['points'] += 1
            t2['points'] += 1
        t1['goal_difference'] = t1['goals_for'] - t1['goals_against']
        t2['goal_difference'] = t2['goals_for'] - t2['goals_against']
    # sort
    return sorted(stats.values(), key=lambda x: (x['points'], x['goal_difference'], x['goals_for']), reverse=True)

def render_three_row_tournament_dashboard(tournament, full_screen: bool = False):
    """Three-row dashboard: 1) sport name, 2) overall points table, 3) per-group match results tables."""
    apply_sport_background(tournament.sport_type.value, fullscreen=full_screen)
    if full_screen:
        apply_fullscreen_chrome()
    # Row 1: sport name
    st.markdown(f"<h1 style='text-align:center;color:var(--text-strong);background:transparent;margin:0.2rem 0 0.2rem;text-shadow:0 1px 0 rgba(255,255,255,0.6);'>{tournament.sport_type.value}</h1>", unsafe_allow_html=True)
    # Compact sizing logic to ensure single-screen fit
    num_teams = len(tournament.teams)
    pad = 10 if num_teams <= 10 else (6 if num_teams <= 16 else (4 if num_teams <= 22 else 3))
    fsize = 14 if num_teams <= 10 else (13 if num_teams <= 16 else (12 if num_teams <= 22 else 11))
    st.markdown(
        f"""
        <style>
        .pro-table tr td, .pro-table tr th {{ padding: {pad}px 8px; line-height: 1.1; font-size: {fsize}px; }}
        .section-title {{ margin: 0.15rem 0; }}
        .subsection-title {{ margin: 0.2rem 0; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Row 2: points table (overall) - only team and points
    st.markdown("<div class='section-title'>جدول النقاط</div>", unsafe_allow_html=True)
    standings = _compute_overall_standings(tournament)
    table = [
        "<table class='pro-table'>",
        "<thead><tr><th>الفريق</th><th>النقاط</th></tr></thead>",
        "<tbody>"
    ]
    for row in standings:
        table.append(f"<tr><td>{row['team_name']}</td><td>{row['points']}</td></tr>")
    table.append("</tbody></table>")
    st.markdown("\n".join(table), unsafe_allow_html=True)
    # Row 3: results per group (single row of tables)
    st.markdown("<div class='section-title'>نتائج المباريات حسب المجموعة</div>", unsafe_allow_html=True)
    if tournament.groups:
        cols = st.columns(max(1, min(4, len(tournament.groups))))
        for i, (gid, group) in enumerate(tournament.groups.items()):
            with cols[i % len(cols)]:
                # Per-group container with sport-themed background tiles
                scene_bg = _sport_scene_tile_data_uri(tournament.sport_type.value)
                emoji_tile = _sport_tile_data_uri(get_sport_icon(tournament.sport_type.value))
                st.markdown(f"<div class='subsection-title' style='margin-bottom:0.25rem;color:var(--text-strong);'>{group.name}</div>", unsafe_allow_html=True)
                group_matches = [m for m in tournament.matches.values() if m.group_id == gid]
                mtable = [
                    "<table class='pro-table'>",
                    "<thead><tr><th>الفريق</th><th>النتيجة</th><th>الفريق</th></tr></thead>",
                    "<tbody>"
                ]
                for m in group_matches:
                    t1 = tournament.teams.get(m.team1_id)
                    t2 = tournament.teams.get(m.team2_id)
                    n1 = t1.name if t1 else '—'
                    n2 = t2.name if t2 else '—'
                    score = f"{m.team1_score} - {m.team2_score}" if m.is_completed else "—"
                    mtable.append(f"<tr><td>{n1}</td><td>{score}</td><td>{n2}</td></tr>")
                mtable.append("</tbody></table>")
                matches_html = "\n".join(mtable)
                st.markdown(
                    f"""
                    <div style='padding:8px;border-radius:12px; background-image: {scene_bg}, {emoji_tile};
                                background-repeat: repeat, repeat; background-size: 180px 180px, 90px 90px; background-color: rgba(255,255,255,0.92);
                                box-shadow: 0 2px 8px rgba(0,0,0,0.06);'>
                        {matches_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("لا توجد مجموعات")

def render_top_navbar():
    """Render a top navigation bar to replace the right sidebar."""
    nav_label_to_page = {
        "الرئيسية": "dashboard",
        "أضف نتائج": "add_results",
        "عرض نتائج": "view_results",
        "أضف فرق": "add_teams",
        "تعديل": "edit_mode",
    }
    tournaments = tm.get_all_tournaments()
    total_teams = sum(len(t.teams) for t in tournaments.values()) if tournaments else 0
    total_matches = sum(len(t.matches) + len(t.knockout_matches) for t in tournaments.values()) if tournaments else 0
    completed_matches = sum(
        sum(1 for m in t.matches.values() if m.is_completed) +
        sum(1 for m in t.knockout_matches.values() if m.is_completed)
        for t in tournaments.values()
    ) if tournaments else 0

    st.markdown(
        """
        <style>
        .top-nav { position: sticky; top: 0; z-index: 10; background: var(--surface); border-bottom: 1px solid var(--border); border-radius: 12px; padding: 6px 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); margin-bottom: 8px; }
        .top-nav-row { display:flex; align-items:center; gap: 8px; }
        .top-brand { display:flex; align-items:center; gap:8px; font-weight:800; }
        .top-stats { display:flex; align-items:center; gap:8px; margin-right:auto; }
        .chip { display:inline-block; padding: 2px 8px; border-radius:999px; background:#eef2f7; color:var(--text); font-size:12px; border:1px solid var(--border); }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown(
            """
            <div class='top-nav'>
              <div class='top-nav-row'>
                <div class='top-brand'>🏆 <span>دوريات نادي الأمين</span></div>
                <div class='top-stats'>
                  <span class='chip'>الدوريات: {tournaments_count}</span>
                  <span class='chip'>الفرق: {teams_count}</span>
                  <span class='chip'>المكتملة: {completed}/{total}</span>
                </div>
              </div>
            </div>
            """.format(
                tournaments_count=len(tournaments) if tournaments else 0,
                teams_count=total_teams,
                completed=completed_matches,
                total=total_matches,
            ),
            unsafe_allow_html=True,
        )
        cols = st.columns([2,2,2,2,2,1])
        labels = list(nav_label_to_page.keys())
        current_page_label = next((k for k, v in nav_label_to_page.items() if v == st.session_state.page), "الرئيسية")
        for i, label in enumerate(labels):
            with cols[i]:
                if st.button(label, use_container_width=True, type=("primary" if label == current_page_label else "secondary")):
                    if nav_label_to_page[label] != st.session_state.page:
                        st.session_state.page = nav_label_to_page[label]
                        st.rerun()

def render_add_results_page():
    """Render add results page"""
    st.title("📝 أضف نتائج")
    
    tournaments = tm.get_all_tournaments()
    
    if not tournaments:
        st.warning("لا توجد دوريات متاحة. يجب إنشاء دوري وإضافة فرق أولاً.")
        return

    # Minimal filters
    filter_options = {"جميع الدوريات": None}
    for t in tournaments.values():
        filter_options[f"{get_sport_icon(t.sport_type.value)} {t.name}"] = t.id
    # Determine default index based on preselection from dashboard
    default_index = 0
    pre_id = st.session_state.get("preselect_add_results_tournament")
    if pre_id:
        labels = list(filter_options.keys())
        for idx, label in enumerate(labels):
            if filter_options[label] == pre_id:
                default_index = idx
                break
        del st.session_state["preselect_add_results_tournament"]
    selected_filter_label = st.selectbox("الدوري", list(filter_options.keys()), index=default_index)
    selected_filter_id = filter_options[selected_filter_label]

    # Get all pending matches (optionally filtered)
    pending_matches = []
    for tournament_id, tournament in tournaments.items():
        if selected_filter_id and tournament_id != selected_filter_id:
            continue
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
    
    st.subheader("اختر المباراة")

    # Build options (no extra previews)
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

    labels = list(match_options.keys())
    # Maintain a simple index for navigation
    if 'addres_idx' not in st.session_state:
        st.session_state.addres_idx = 0
    # Reset index when tournament filter changes
    if st.session_state.addres_idx >= len(labels):
        st.session_state.addres_idx = 0
    # Mobile-responsive match selection
    col_sel, col_next = st.columns([3,1])
    with col_sel:
        selected_match_label = st.selectbox("المباراة", labels, index=st.session_state.addres_idx)
    with col_next:
        if st.button("التالي", use_container_width=True):
            st.session_state.addres_idx = (labels.index(selected_match_label) + 1) % len(labels)
            st.rerun()
    
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
        
        # Mobile-responsive quick actions
        st.markdown("**اختر النتيجة:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"🏆 فوز {team1_name}", key="team1_win", use_container_width=True, type="primary"):
                # Team 1 wins: 1-0
                if tm.update_match_result(selected_item['tournament_id'], match.id, 1, 0):
                    st.success(f"تم تسجيل فوز {team1_name}!")
                    st.session_state.addres_idx = (labels.index(selected_match_label) + 1) % len(labels)
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("فشل في تحديث النتيجة")
        
        with col2:
            if st.button("🤝 تعادل", key="draw", use_container_width=True, type="secondary"):
                # Draw: 0-0
                if tm.update_match_result(selected_item['tournament_id'], match.id, 0, 0):
                    st.success("تم تسجيل التعادل!")
                    st.session_state.addres_idx = (labels.index(selected_match_label) + 1) % len(labels)
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("فشل في تحديث النتيجة")
        
        with col3:
            if st.button(f"🏆 فوز {team2_name}", key="team2_win", use_container_width=True, type="primary"):
                # Team 2 wins: 0-1
                if tm.update_match_result(selected_item['tournament_id'], match.id, 0, 1):
                    st.success(f"تم تسجيل فوز {team2_name}!")
                    st.session_state.addres_idx = (labels.index(selected_match_label) + 1) % len(labels)
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("فشل في تحديث النتيجة")

        # Mobile-responsive custom score section
        with st.expander("نتيجة مخصصة"):
            # Mobile: stack vertically, desktop: horizontal
            col1, col2 = st.columns(2)
            with col1:
                team1_score = st.number_input("نتيجة الفريق 1", min_value=0, step=1, key=f"cust_t1_{match.id}")
            with col2:
                team2_score = st.number_input("نتيجة الفريق 2", min_value=0, step=1, key=f"cust_t2_{match.id}")
            
            if st.button("تحديث النتيجة", type="primary", key=f"cust_update_{match.id}", use_container_width=True):
                if tm.update_match_result(selected_item['tournament_id'], match.id, int(team1_score), int(team2_score)):
                    st.success("تم تحديث النتيجة!")
                    st.session_state.addres_idx = (labels.index(selected_match_label) + 1) % len(labels)
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("فشل في تحديث النتيجة")

def render_view_results_page():
    """Render view results page"""
    if not (st.session_state.viewing_mode == "automatic" and st.session_state.auto_mode_running):
        st.title("📺 عرض نتائج")
    
    tournaments = tm.get_all_tournaments()
    
    if not tournaments:
        st.info("لا توجد دوريات متاحة للعرض.")
        return
    
    # Handle query param actions for auto slideshow controls (exit/mode/interval)
    try:
        params = dict(st.query_params) if hasattr(st, "query_params") else st.experimental_get_query_params()
    except Exception:
        params = {}
    def _clear_params():
        try:
            if hasattr(st, "query_params"):
                st.query_params.clear()
            else:
                st.experimental_set_query_params()
        except Exception:
            pass
    if params:
        # Normalize single values
        def _getv(k):
            v = params.get(k)
            return v[0] if isinstance(v, list) else v
        exit_flag = _getv("exit")
        mode_val = _getv("mode")
        interval_val = _getv("interval")
        prev_flag = _getv("prev")
        next_flag = _getv("next")
        
        if exit_flag:
            st.session_state.auto_mode_running = False
            st.session_state.viewing_mode = "manual"
            _clear_params()
            st.rerun()
        if prev_flag:
            st.session_state.current_slide -= 1
            _clear_params()
            st.rerun()
        if next_flag:
            st.session_state.current_slide += 1
            _clear_params()
            st.rerun()
        if mode_val in ("manual", "automatic"):
            st.session_state.viewing_mode = mode_val
            if mode_val == "manual":
                st.session_state.auto_mode_running = False
            _clear_params()
            st.rerun()
        if interval_val:
            try:
                iv = int(interval_val)
                iv = max(5, min(60, iv))
                st.session_state.slideshow_interval = iv
            except Exception:
                pass
            _clear_params()
            st.rerun()

    # Viewing mode selection (hidden during running automatic slideshow)
    show_top_controls = not (st.session_state.viewing_mode == "automatic" and st.session_state.auto_mode_running)
    viewing_mode = st.session_state.viewing_mode
    if show_top_controls:
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
        
        # No top separator while in view results page; keep top tight
    
    if viewing_mode == "manual":
        # Manual viewing mode
        st.subheader("اختر الدوري للعرض")
        
        tournament_options = {f"{get_sport_icon(t.sport_type.value)} {t.name}": t.id for t in tournaments.values()}
        # Default selection from dashboard quick action
        default_index = 0
        pre_id = st.session_state.get("preselect_tournament")
        if pre_id:
            labels = list(tournament_options.keys())
            for idx, label in enumerate(labels):
                if tournament_options[label] == pre_id:
                    default_index = idx
                    break
            del st.session_state["preselect_tournament"]
        selected_tournament_label = st.selectbox("الدوري", list(tournament_options.keys()), index=default_index)
        
        if selected_tournament_label:
            selected_tournament_id = tournament_options[selected_tournament_label]
            selected_tournament = tournaments[selected_tournament_id]
            # Three-row tournament dashboard in embedded mode (keeps navigation/sidebar)
            render_three_row_tournament_dashboard(selected_tournament, full_screen=False)
            return
    
    else:
        # Automatic viewing mode
        if not st.session_state.auto_mode_running:
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("▶️ بدء العرض التلقائي", type="primary"):
                    st.session_state.auto_mode_running = True
                    st.rerun()
            with col2:
                if st.button("⏹️ إيقاف العرض التلقائي", type="secondary"):
                    st.session_state.auto_mode_running = False
                    st.rerun()
            with col3:
                randomize = st.checkbox("ترتيب عشوائي", value=st.session_state.get("randomize_slideshow", False))
                st.session_state.randomize_slideshow = randomize
        
        if st.session_state.auto_mode_running:
            tournament_list = list(tournaments.values())
            if tournament_list:
                # Build slide sequence (groups + knockout per tournament)
                slides = _build_auto_slides(tournament_list)
                if not slides:
                    st.info("لا توجد شرائح للعرض")
                    return
                # Determine current slide
                if st.session_state.get("randomize_slideshow", False):
                    tid, kind, payload = random.choice(slides)
                    # keep current_slide moving for counter feel
                    st.session_state.current_slide += 1
                else:
                    idx = st.session_state.current_slide % len(slides)
                    tid, kind, payload = slides[idx]
                current_tournament = tournaments.get(tid)
                if not current_tournament:
                    # Skip invalid and advance
                    st.session_state.current_slide += 1
                    st.rerun()
                # Apply fullscreen chrome and sport background for slide feel
                apply_sport_background(current_tournament.sport_type.value, fullscreen=True)
                apply_fullscreen_chrome()
                # Determine scale to fit into one viewport without scrolling
                s_count = 0
                m_count = 0
                if kind == 'group' and payload in current_tournament.groups:
                    try:
                        s_count = len(current_tournament.get_group_standings(payload))
                        m_count = sum(1 for m in current_tournament.matches.values() if m.group_id == payload)
                    except Exception:
                        s_count = 0
                        m_count = 0
                elif kind == 'knockout':
                    try:
                        m_count = len(current_tournament.knockout_matches)
                    except Exception:
                        m_count = 0
                elif kind == 'groups_chunk':
                    try:
                        s_count = sum(len(current_tournament.get_group_standings(gid)) for gid in payload)
                        m_count = sum(1 for m in current_tournament.matches.values())
                    except Exception:
                        s_count = 0
                        m_count = 0
                total_rows = s_count + m_count
                scale_val = 1.0
                if total_rows > 18:
                    scale_val = 0.95
                if total_rows > 26:
                    scale_val = 0.9
                if total_rows > 34:
                    scale_val = 0.85
                if total_rows > 42:
                    scale_val = 0.8
                if total_rows > 50:
                    scale_val = 0.75
                if total_rows > 60:
                    scale_val = 0.7
                if total_rows > 75:
                    scale_val = 0.65
                if total_rows > 90:
                    scale_val = 0.6
                if total_rows > 110:
                    scale_val = 0.55
                if total_rows > 140:
                    scale_val = 0.5
                # Dynamic compact table/card styles based on density
                comp_pad = 6
                comp_font = 12
                card_pad = 10
                if total_rows > 60:
                    comp_pad = 5
                    comp_font = 11
                    card_pad = 8
                if total_rows > 90:
                    comp_pad = 4
                    comp_font = 10
                    card_pad = 6
                # Slide styling: fade-in and animated progress bar matching interval
                interval = max(1, int(st.session_state.slideshow_interval))
                total_slides = len(slides)
                current_number = (st.session_state.current_slide % total_slides) + 1 if total_slides else 1
                st.markdown(
                    f"""
                    <style>
                    @keyframes slideFadeIn {{
                        from {{ opacity: 0; transform: translateY(6px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    @keyframes slideProgress {{
                        from {{ width: 0%; }}
                        to {{ width: 100%; }}
                    }}
                    .autoslide-overlay {{
                        position: fixed; inset: 0; z-index: 9999;
                        display: flex; flex-direction: column; align-items: center; justify-content: flex-start;
                        overflow: hidden; padding: 0 8px 0 8px;
                    }}
                    .autoslide-canvas {{
                        width: 100%; max-width: 1200px;
                        transform: scale({scale_val}); transform-origin: top center;
                        animation: slideFadeIn 300ms ease both;
                    }}

                    /* Compact overrides for group cards/tables to reduce height */
                    .group-card {{ padding: {card_pad}px; }}
                    .group-card .pro-table.compact th, .group-card .pro-table.compact td {{ padding: {comp_pad}px 6px; font-size: {comp_font}px; }}
                    .section-title {{ margin: 0.2rem 0; }}
                    .subsection-title {{ margin: 0.2rem 0; }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                # Render slide content without overlay
                _render_auto_slide(current_tournament, kind, payload)
                
                # Control buttons in normal flow
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("⬅️ السابق", key="prev_btn"):
                        st.session_state.current_slide -= 1
                        # Reset timer to sync with manual navigation
                        st.session_state.last_advance_time = time.time()
                        st.rerun()
                
                with col2:
                    if st.button("التالي ➡️", key="next_btn"):
                        st.session_state.current_slide += 1
                        # Reset timer to sync with manual navigation
                        st.session_state.last_advance_time = time.time()
                        st.rerun()
                
                with col3:
                    if st.button("⤴️ خروج", key="exit_btn"):
                        st.session_state.auto_mode_running = False
                        st.session_state.viewing_mode = "manual"
                        st.rerun()
                
                # Synchronized auto-advance timer
                if st.session_state.get("last_advance_time", 0) + interval <= time.time():
                    st.session_state.current_slide += 1
                    st.session_state.last_advance_time = time.time()
                    st.rerun()
                else:
                    # Keep the page responsive by using a short sleep
                    time.sleep(0.1)
                    st.rerun()
        else:
            st.info("اضغط على 'بدء العرض التلقائي' لبدء العرض التلقائي للدوريات")
            st.subheader("الدوريات المتاحة")
            # Compact list view with chips
            for tournament in tournaments.values():
                st.markdown(
                    f"<div class='ux-card' style='margin-bottom:0.5rem; display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div>{get_sport_icon(tournament.sport_type.value)} {tournament.name}</div>"
                    f"<span class='chip chip-accent'>{tournament.sport_type.value}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

def render_add_teams_page():
    """Render add teams page"""
    st.title("👥 أضف فرق")
    
    tab1, tab2, tab3 = st.tabs(["إضافة الفرق", "إدارة الفرق", "إدارة المواجهات"])
    
    with tab1:
        st.subheader("إضافة فريق/لاعب جديد")

        with st.form(key="create_tournament_form"):
            col1, col2 = st.columns(2)
            with col1:
                tournament_name = st.text_input("اسم الدوري", key="tournament_name_create")
                sport_options = [sport.value for sport in SportType]
                selected_sport = st.selectbox("نوع الرياضة", sport_options, key="selected_sport_create")
            with col2:
                add_mode = st.radio("طريقة الإضافة", ["فريق واحد", "عدة فرق"], horizontal=True, key="add_mode_create")
                if add_mode == "فريق واحد":
                    team_name_label = get_team_name_label(selected_sport)
                    team_name = st.text_input(team_name_label, key="team_name_create")
                else:
                    st.caption("أدخل كل اسم في سطر منفصل")
                    bulk_names = st.text_area("الأسماء", height=150, key="bulk_names_create")
            
            # Live preview card
            preview_cols = st.columns([2, 1])
            with preview_cols[0]:
                team_preview = team_name.strip() if ("team_name" in locals() and team_name) else "—"
                bulk_count = len([n for n in (bulk_names.splitlines() if "bulk_names" in locals() and bulk_names else []) if n.strip()])
                st.markdown(f"""
                    <div class='ux-card ux-card-accent'>
                        <div style='font-weight:800;'>{tournament_name if tournament_name else "اسم الدوري"}</div>
                        <div class='ux-muted' style='margin:0.25rem 0;'>الرياضة: {selected_sport}</div>
                        <div>{'👥 فريق واحد: ' + team_preview if add_mode == 'فريق واحد' else '👥 عدد الفرق: ' + str(bulk_count)}</div>
                    </div>
                """, unsafe_allow_html=True)
            with preview_cols[1]:
                notes = st.text_area("ملاحظات (اختياري)", key="notes_create")

            submitted = st.form_submit_button("إنشاء الدوري وإضافة الفرق", type="primary", use_container_width=True)
            if submitted:
                if not tournament_name.strip():
                    st.error("يرجى إدخال اسم الدوري")
                elif add_mode == "فريق واحد" and not team_name.strip():
                    st.error("يرجى إدخال اسم الفريق/اللاعب")
                elif add_mode == "عدة فرق" and not bulk_names.strip():
                    st.error("يرجى إدخال الأسماء")
                else:
                    sport_type = SportType(selected_sport)
                    tournament_created = tm.create_tournament(tournament_name.strip(), sport_type)
                    if tournament_created:
                        tournaments_all = tm.get_all_tournaments()
                        created_tournament = None
                        for t in tournaments_all.values():
                            if t.name == tournament_name.strip() and t.sport_type == sport_type:
                                created_tournament = t
                                break
                        success_count = 0
                        total = 0
                        if created_tournament:
                            if add_mode == "فريق واحد":
                                total = 1
                                if tm.add_team_to_tournament(created_tournament.id, team_name.strip()):
                                    success_count = 1
                            else:
                                names = [n.strip() for n in bulk_names.splitlines() if n.strip()]
                                total = len(names)
                                for name in names:
                                    if tm.add_team_to_tournament(created_tournament.id, name):
                                        success_count += 1
                        if success_count > 0:
                            st.success(f"تم إنشاء الدوري '{tournament_name}' وإضافة {success_count} من {total} بنجاح!")
                            st.rerun()
                        else:
                            st.error("فشل في إضافة أي فريق")
                    else:
                        st.error("فشل في إنشاء الدوري")
    
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
                    
                    if st.button("إضافة الفريق", type="primary", key="add_to_existing", use_container_width=True):
                        if new_team_name.strip():
                            if tm.add_team_to_tournament(selected_tournament_id, new_team_name.strip()):
                                st.success("تم إضافة الفريق بنجاح!")
                                st.rerun()
                            else:
                                st.error("فشل في إضافة الفريق")
                        else:
                            st.error("يرجى إدخال اسم الفريق")

                # Bulk add teams
                with st.expander("إضافة عدة فرق دفعة واحدة"):
                    st.caption("أدخل كل اسم في سطر منفصل")
                    bulk_text = st.text_area("الأسماء", height=150, key="bulk_team_text")
                    if st.button("إضافة الكل", type="primary", key="bulk_add_btn", use_container_width=True):
                        names = [n.strip() for n in bulk_text.splitlines() if n.strip()]
                        if not names:
                            st.warning("لم يتم العثور على أسماء.")
                        else:
                            success_count = 0
                            for name in names:
                                if tm.add_team_to_tournament(selected_tournament_id, name):
                                    success_count += 1
                            st.success(f"تمت إضافة {success_count} من {len(names)}.")
                            st.rerun()
                
                # Display and manage existing teams
                if tournament.teams:
                    st.subheader("الفرق المسجلة")
                    search_query = st.text_input("ابحث عن فريق", key="team_search")
                    
                    # Sort and filter
                    teams_sorted = sorted(tournament.teams.items(), key=lambda kv: kv[1].name)
                    for team_id, team in teams_sorted:
                        if search_query and search_query.strip() not in team.name:
                            continue
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**{team.name}**")
                        
                        with col2:
                            if st.button("حذف", key=f"delete_team_{team_id}", type="secondary", use_container_width=True):
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
        if st.button("🏆 إدارة الدوريات", use_container_width=True, type="primary"):
            st.session_state.page = "tournament_management"
            st.rerun()
        
        st.markdown("إدارة الدوريات، إنشاء دوريات جديدة، حذف الدوريات الموجودة")
    
    with col2:
        if st.button("⚙️ الإعدادات المتقدمة", use_container_width=True, type="secondary"):
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
    """Render a clean, professional tournament results view (type, standings, all matches)."""
    # Header
    header_tag = "h1" if full_screen else "h2"
    st.markdown(
        f"<{header_tag} style='text-align:center;margin-bottom:0.5rem;'>{get_sport_icon(tournament.sport_type.value)} {tournament.name}</{header_tag}>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div style='text-align:center;margin-bottom:1rem;'><span class='chip chip-accent'>{tournament.sport_type.value}</span></div>", unsafe_allow_html=True)

    # Groups: standings + all matches
    if tournament.groups:
        st.markdown("<div class='section-title'>🏁 دور المجموعات</div>", unsafe_allow_html=True)
        for group_id, group in tournament.groups.items():
            st.markdown(f"<div class='subsection-title'>{group.name}</div>", unsafe_allow_html=True)
            standings = tournament.get_group_standings(group_id)
            # Standings table (Team, Points)
            table = [
                "<table class='pro-table'>",
                "<thead><tr><th>الفريق</th><th>النقاط</th></tr></thead>",
                "<tbody>"
            ]
            for row in standings:
                table.append(f"<tr><td>{row['team_name']}</td><td>{row['points']}</td></tr>")
            table.append("</tbody></table>")
            st.markdown("\n".join(table), unsafe_allow_html=True)

            # Group matches table
            group_matches = [m for m in tournament.matches.values() if m.group_id == group_id]
            st.markdown(f"<div class='subsection-title'>نتائج المباريات</div>", unsafe_allow_html=True)
            if group_matches:
                mtable = [
                    "<table class='pro-table'>",
                    "<thead><tr><th>الفريق 1</th><th>النتيجة</th><th>الفريق 2</th></tr></thead>",
                    "<tbody>"
                ]
                for m in group_matches:
                    t1 = tournament.teams.get(m.team1_id)
                    t2 = tournament.teams.get(m.team2_id)
                    n1 = t1.name if t1 else '—'
                    n2 = t2.name if t2 else '—'
                    score = f"{m.team1_score} - {m.team2_score}" if m.is_completed else "—"
                    mtable.append(f"<tr><td>{n1}</td><td>{score}</td><td>{n2}</td></tr>")
                mtable.append("</tbody></table>")
                st.markdown("\n".join(mtable), unsafe_allow_html=True)
            else:
                st.info("لا توجد مباريات في هذه المجموعة")

    # Knockout matches
    if tournament.knockout_matches:
        st.markdown("<div class='section-title'>🏆 دور الإقصاء</div>", unsafe_allow_html=True)
        rounds = {}
        for match in tournament.knockout_matches.values():
            rounds.setdefault(match.round_type, []).append(match)
        for round_type in ["semi", "final"]:
            if round_type in rounds:
                st.markdown(f"<div class='subsection-title'>{get_round_name(round_type)}</div>", unsafe_allow_html=True)
                ktable = [
                    "<table class='pro-table'>",
                    "<thead><tr><th>الفريق 1</th><th>النتيجة</th><th>الفريق 2</th></tr></thead>",
                    "<tbody>"
                ]
                for m in rounds[round_type]:
                    t1 = tournament.teams.get(m.team1_id)
                    t2 = tournament.teams.get(m.team2_id)
                    n1 = t1.name if t1 else '—'
                    n2 = t2.name if t2 else '—'
                    score = f"{m.team1_score} - {m.team2_score}" if m.is_completed else "—"
                    ktable.append(f"<tr><td>{n1}</td><td>{score}</td><td>{n2}</td></tr>")
                ktable.append("</tbody></table>")
                st.markdown("\n".join(ktable), unsafe_allow_html=True)

def render_dashboard():
    """Render main dashboard"""
    # Always render dashboard in a single view with auto-compact scaling
    tournaments = tm.get_all_tournaments()
    num_tournaments = len(tournaments)
    num_groups = sum(len(t.groups) for t in tournaments.values())
    # Heuristic scale to fit content in one view
    scale = 90
    if num_tournaments > 3 or num_groups > 6:
        scale = 85
    if num_tournaments > 5 or num_groups > 10:
        scale = 80
    if num_tournaments > 8 or num_groups > 14:
        scale = 75
    if num_tournaments > 10 or num_groups > 18:
        scale = 70
    if num_tournaments > 12 or num_groups > 22:
        scale = 65
    if num_tournaments > 15 or num_groups > 26:
        scale = 60
    apply_compact_no_scroll(scale)
    # Zero top spacing for a flush top and tighten heading spacing
    st.markdown(
        """
        <style>
        .block-container { padding-top: 0 !important; margin-top: 0 !important; }
        h1, h2, h3 { margin-top: 0 !important; margin-bottom: 0.25rem !important; }
        .stMetric { padding: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Header section
    st.markdown("<h1 style='text-align: center; color: var(--brand-primary); margin:0;'>🏆 نادي الأمين</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin: 0 0 0.5rem 0;'>أهلاً بكم</h3>", unsafe_allow_html=True)
    
    # Main buttons section
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 أضف نتائج", key="add_results", use_container_width=True, type="primary"):
            st.session_state.page = "add_results"
            st.rerun()
    with col2:
        if st.button("📺 عرض نتائج", key="view_results", use_container_width=True, type="primary"):
            st.session_state.page = "view_results"
            st.rerun()
    with col3:
        if st.button("👥 أضف فرق", key="add_teams", use_container_width=True, type="primary"):
            st.session_state.page = "add_teams"
            st.rerun()
    with col4:
        if st.button("🤝 إدارة المباريات", key="manage_matches_hub", use_container_width=True, type="secondary"):
            st.session_state.page = "match_hub"
            st.rerun()
    
    # Edit button (no top separator)
    st.markdown("---")
    col_edit = st.columns([1, 2, 1])
    with col_edit[1]:
        if st.button("⚙️ تعديل", key="edit_main", use_container_width=True, type="secondary"):
            st.session_state.page = "edit_mode"
            st.rerun()
    
    # Show quick stats if tournaments exist
    if tournaments:
        # No top separator; go straight to content
        st.subheader("نظرة سريعة")
        
        # Quick statistics
        total_teams = sum(len(t.teams) for t in tournaments.values())
        total_matches = sum(len(t.matches) + len(t.knockout_matches) for t in tournaments.values())
        completed_matches = sum(
            sum(1 for m in t.matches.values() if m.is_completed) +
            sum(1 for m in t.knockout_matches.values() if m.is_completed)
            for t in tournaments.values()
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("عدد الدوريات", len(tournaments))
        with col2:
            st.metric("إجمالي الفرق", total_teams)
        with col3:
            st.metric("المباريات المكتملة", f"{completed_matches}/{total_matches}")

        # Tournament cards grid with search/sort/filters/view toggle
        st.subheader("الدوريات النشطة")
        control_cols = st.columns([2,2,2,2,2])
        with control_cols[0]:
            search_query = st.text_input("ابحث عن دوري", key="dash_search")
        with control_cols[1]:
            sort_by = st.selectbox("ترتيب حسب", ["الاسم", "عدد الفرق", "نسبة الإنجاز"], key="dash_sort_by")
        with control_cols[2]:
            sort_dir_desc = st.checkbox("تنازلي", value=False, key="dash_sort_desc")
        with control_cols[3]:
            sport_filter = st.selectbox("الرياضة", ["الكل"] + [s.value for s in SportType], key="dash_sport")
        with control_cols[4]:
            only_pending = st.checkbox("مباريات معلّقة فقط", value=False, key="dash_only_pending")

        tournaments_list = list(tournaments.values())
        if search_query:
            q = search_query.strip()
            tournaments_list = [t for t in tournaments_list if q in t.name]
        if sport_filter != "الكل":
            tournaments_list = [t for t in tournaments_list if t.sport_type.value == sport_filter]
        def completion_ratio(t):
            total = len(t.matches) + len(t.knockout_matches)
            if total == 0:
                return 0
            done = sum(1 for m in t.matches.values() if m.is_completed) + sum(1 for m in t.knockout_matches.values() if m.is_completed)
            return done/total
        if only_pending:
            tournaments_list = [t for t in tournaments_list if completion_ratio(t) < 1]
        if sort_by == "الاسم":
            tournaments_list.sort(key=lambda t: t.name, reverse=sort_dir_desc)
        elif sort_by == "عدد الفرق":
            tournaments_list.sort(key=lambda t: len(t.teams), reverse=sort_dir_desc)
        else:
            tournaments_list.sort(key=completion_ratio, reverse=sort_dir_desc)
        view_mode = st.radio("العرض", ["شبكة", "قائمة"], index=0, key="dash_view_mode")
        num_cols = 3 if view_mode == "شبكة" else 1
        rows = (len(tournaments_list) + num_cols - 1) // num_cols
        idx = 0
        for _ in range(rows):
            cols = st.columns(num_cols)
            for c in range(num_cols):
                if idx >= len(tournaments_list):
                    break
                t = tournaments_list[idx]
                with cols[c]:
                    group_matches_completed = sum(1 for m in t.matches.values() if match_completed(m))
                    knockout_matches_completed = sum(1 for m in t.knockout_matches.values() if match_completed(m))
                    total_matches = len(t.matches) + len(t.knockout_matches)
                    done = group_matches_completed + knockout_matches_completed
                    ratio = (done / total_matches) if total_matches else 0
                    size_style = "" if view_mode == "شبكة" else "display:flex;align-items:center;gap:1rem;"
                    st.markdown(f"""
                        <div class='ux-card ux-card-accent' style='{size_style}'>
                            <div style='flex:1;'>
                                <div style='display:flex;align-items:center;justify-content:space-between;'>
                                    <div style='font-weight:800;'>{get_sport_icon(t.sport_type.value)} {t.name}</div>
                                    <span class='chip chip-accent'>{t.sport_type.value}</span>
                                </div>
                                <div style='margin-top:0.5rem; display:flex; gap:0.75rem; font-size:0.9rem; flex-wrap:wrap;'>
                                    <div>👥 {len(t.teams)} فريق</div>
                                    <div>📊 المجموعات: {group_matches_completed}/{len(t.matches)}</div>
                                    <div>🥇 الإقصاء: {knockout_matches_completed}/{len(t.knockout_matches)}</div>
                                </div>
                                <div style='margin-top:0.5rem;'>
                                    <div style='height:8px;background:var(--border);border-radius:999px;overflow:hidden;'>
                                        <div style='width:{ratio*100:.0f}%;height:100%;background:var(--brand-primary);'></div>
                                    </div>
                                    <div class='ux-muted' style='font-size:0.8rem;margin-top:0.25rem;'>نسبة الإنجاز: {int(ratio*100)}%</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("📺 عرض", key=f"dash_view_{t.id}", use_container_width=True):
                            st.session_state.preselect_tournament = t.id
                            st.session_state.page = "view_results"
                            st.rerun()
                    with b2:
                        if st.button("📝 إضافة نتيجة", key=f"dash_addres_{t.id}", use_container_width=True):
                            st.session_state.preselect_add_results_tournament = t.id
                            st.session_state.page = "add_results"
                            st.rerun()
                    b3, b4 = st.columns(2)
                    with b3:
                        if st.button("👥 إدارة الفرق", key=f"dash_team_{t.id}", use_container_width=True):
                            st.session_state.current_tournament = t.id
                            st.session_state.page = "team_management"
                            st.rerun()
                    with b4:
                        if st.button("🤝 إدارة المباريات", key=f"dash_match_{t.id}", use_container_width=True):
                            st.session_state.current_tournament = t.id
                            st.session_state.page = "match_management"
                            st.rerun()
                idx += 1
        # Group tables section on dashboard
        st.markdown("---")
        st.subheader("جداول المجموعات")
        for t_id, t in tournaments.items():
            if t.groups:
                with st.container():
                    st.markdown(
                        f"<div class='section-title'>{get_sport_icon(t.sport_type.value)} {t.name}</div>",
                        unsafe_allow_html=True,
                    )
                    # Render this tournament's groups inside an isolated grid container
                    scene_bg = _sport_scene_tile_data_uri(t.sport_type.value)
                    emoji_tile = _sport_tile_data_uri(get_sport_icon(t.sport_type.value))
                    groups = list(t.groups.items())
                    per_row = max(1, min(4, len(groups)))
                    for row_start in range(0, len(groups), per_row):
                        cols = st.columns(per_row)
                        for j, (gid, group) in enumerate(groups[row_start:row_start+per_row]):
                            with cols[j]:
                                standings = t.get_group_standings(gid)
                                table_lines = [
                                    "<table class='pro-table'>",
                                    "<thead><tr><th>الفريق</th><th>النقاط</th></tr></thead>",
                                    "<tbody>"
                                ]
                                for row in standings:
                                    table_lines.append(f"<tr><td>{row['team_name']}</td><td>{row['points']}</td></tr>")
                                table_lines.append("</tbody></table>")
                                table_html = "\n".join(table_lines)
                                container_html = f"""
                                <div style='padding:8px;border-radius:12px;
                                            background-image: {scene_bg}, {emoji_tile};
                                            background-repeat: repeat, repeat;
                                            background-size: 180px 180px, 90px 90px;
                                            background-color: rgba(255,255,255,0.92);
                                            box-shadow: 0 2px 8px rgba(0,0,0,0.06);'>
                                    <div class='subsection-title' style='margin:0 0 0.25rem 0;color:var(--text-strong);'>{group.name}</div>
                                    {table_html}
                                </div>
                                """
                                st.markdown(container_html, unsafe_allow_html=True)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    else:
        st.markdown("---")
        st.markdown(
            """
            <div class='ux-card ux-card-accent' style='text-align:center;'>
                <div style='font-weight:800; margin-bottom:0.5rem;'>لا توجد دوريات بعد</div>
                <div class='ux-muted'>ابدأ بإضافة فرق/لاعبين لإنشاء أول دوري لك</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cta_col = st.columns([1,2,1])[1]
        with cta_col:
            if st.button("➕ ابدأ بإضافة فرق", type="primary", use_container_width=True):
                st.session_state.page = "add_teams"
                st.rerun()

def main():
    """Main application function"""
    # Global UI baseline
    inject_global_styles()
    # Only show navbar on interactive pages, not on dashboard or auto slideshow
    show_navbar = True
    try:
        if st.session_state.page == "dashboard":
            show_navbar = False
        elif st.session_state.page == "view_results" and st.session_state.viewing_mode == "automatic" and st.session_state.auto_mode_running:
            show_navbar = False
    except Exception:
        pass
    if show_navbar:
        render_top_navbar()
    # (Top back button removed to avoid whitespace)

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

    elif st.session_state.page == "match_hub":
        # Simple hub to select a tournament for match management
        st.title("🤝 إدارة المباريات")
        tournaments = tm.get_all_tournaments()
        if tournaments:
            options = {f"{get_sport_icon(t.sport_type.value)} {t.name}": tid for tid, t in tournaments.items()}
            selected = st.selectbox("اختر الدوري", list(options.keys()))
            if st.button("انتقال", type="primary"):
                st.session_state.current_tournament = options[selected]
                st.session_state.page = "match_management"
                st.rerun()
        else:
            st.info("لا توجد دوريات متاحة")

    # Bottom back-to-home button on all non-dashboard pages
    if st.session_state.page != "dashboard":
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🏠 العودة للرئيسية", type="secondary"):
            st.session_state.page = "dashboard"
            if 'current_tournament' in st.session_state:
                del st.session_state.current_tournament
            st.rerun()

if __name__ == "__main__":
    main()
