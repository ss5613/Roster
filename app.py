"""
app.py — ShiftPulse: Shift Management & Workforce Availability Dashboard
=========================================================================
A premium Streamlit application for employee shift management,
real-time workforce tracking, and availability analytics.

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time, timedelta
import os
import calendar as cal

from data_loader import (
    load_and_process_all,
    get_employee_status,
    get_all_support_types,
    is_available,
    classify_real_time,
    SHIFT_COLORS,
    SHIFT_COLOR_BG,
    UNAVAILABLE_CODES,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.set_page_config(
    page_title="ShiftPulse — Workforce Manager",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CUSTOM CSS — Premium glassmorphism dark theme
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<style>
    /* ── Import Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ── Root variables ── */
    :root {
        --bg-primary: #0f0f1a;
        --bg-card: rgba(22, 22, 40, 0.85);
        --bg-card-hover: rgba(30, 30, 55, 0.95);
        --border-glow: rgba(99, 102, 241, 0.3);
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --accent-indigo: #818cf8;
        --accent-violet: #a78bfa;
        --accent-emerald: #34d399;
        --accent-rose: #fb7185;
        --accent-amber: #fbbf24;
        --glass-border: rgba(255, 255, 255, 0.08);
        --shadow-glow: 0 0 30px rgba(99, 102, 241, 0.1);
    }
    
    /* ── Global ── */
    .stApp {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #13132b 100%) !important;
        border-right: 1px solid var(--glass-border);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label {
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* ── Headers ── */
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* ── Metric Cards ── */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--border-glow);
        transform: translateY(-2px);
        box-shadow: 0 8px 40px rgba(99, 102, 241, 0.15);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        font-size: 2rem !important;
    }
    
    /* ── DataFrames ── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(15, 15, 30, 0.5);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 20px;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        color: white !important;
    }
    
    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        border: none;
        border-radius: 10px;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        padding: 8px 24px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    }
    
    /* ── Custom card class ── */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: var(--shadow-glow);
    }
    .glass-card:hover {
        border-color: var(--border-glow);
    }
    
    /* ── Calendar ── */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 6px;
        margin-top: 12px;
    }
    .cal-header {
        text-align: center;
        font-weight: 700;
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 8px 0;
    }
    .cal-day {
        aspect-ratio: 1;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid var(--glass-border);
        transition: all 0.25s ease;
        cursor: pointer;
        min-height: 60px;
    }
    .cal-day:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .cal-day .day-num {
        font-size: 0.95rem;
        font-weight: 700;
    }
    .cal-day .shift-label {
        font-size: 0.65rem;
        font-weight: 600;
        margin-top: 2px;
        opacity: 0.9;
    }
    .cal-empty {
        aspect-ratio: 1;
        min-height: 60px;
    }
    .cal-today {
        border: 2px solid #818cf8 !important;
        box-shadow: 0 0 15px rgba(129, 140, 248, 0.3);
    }
    
    /* ── Hero header ── */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 24px;
    }
    
    /* ── Section headers ── */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* ── Divider ── */
    .gradient-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #4f46e5, #7c3aed, transparent);
        border: none;
        margin: 24px 0;
        border-radius: 2px;
    }
    
    /* ── Hide Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA LOADING (cached)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Shift draft (1).xlsx")


@st.cache_data(ttl=300)
def load_data():
    """Load and process all data from Excel. Cached for 5 minutes."""
    return load_and_process_all(EXCEL_PATH)


def get_shift_color(code: str) -> str:
    """Get color for a shift code, with fallback."""
    return SHIFT_COLORS.get(str(code).strip().upper(), "#64748b")


def get_shift_bg(code: str) -> str:
    """Get background color for a shift code, with fallback."""
    return SHIFT_COLOR_BG.get(str(code).strip().upper(), "rgba(100,116,139,0.15)")


def get_timing_str(code: str, shift_lookup: dict) -> str:
    """Get formatted timing string for a shift code."""
    c = str(code).strip().upper()
    if c in shift_lookup:
        sl = shift_lookup[c]
        # Use the original timing_str if available, else compose from start/end
        if sl.get("timing_str") and sl["timing_str"] not in ("", "nan", "None"):
            return sl["timing_str"]
        return f"{sl['start_str']} - {sl['end_str']}"
    return "—"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    employee_master, shift_data, shift_timings, shift_lookup = load_data()
    data_loaded = True
except Exception as e:
    data_loaded = False
    st.error(f"❌ Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
    st.info("Make sure the Excel file `Shift draft (1).xlsx` is in the same folder as this app.")
    st.stop()

# Get unique values for filters
all_employees = sorted(shift_data["Associate Name"].unique().tolist()) if not shift_data.empty else []
all_shifts = sorted([
    c for c in shift_data["Shift Code"].unique()
    if c and c not in ("", "NAN", "NONE")
]) if not shift_data.empty else []

# Get unique support types from employee master (across all Support columns)
all_support_types = get_all_support_types(employee_master) if not employee_master.empty else []

all_locations = sorted([
    l for l in shift_data["Location"].unique() if l != "N/A"
]) if "Location" in shift_data.columns else []

all_dates = sorted(
    shift_data["Date"].dropna().unique().tolist()
) if not shift_data.empty else []

today = date.today()
current_time = datetime.now().time()


def filter_by_support_type(df: pd.DataFrame, support_type: str) -> pd.DataFrame:
    """Filter shift_data rows where the employee has the given support type in any Support column."""
    if "All Support Types" not in df.columns:
        return df
    return df[df["All Support Types"].apply(
        lambda types: support_type.upper() in [t.upper() for t in types] if isinstance(types, list) else False
    )]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown('<div class="hero-title">⚡ ShiftPulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Workforce Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Quick stats
    st.markdown("##### 📊 Data Overview")
    col1, col2 = st.columns(2)
    col1.metric("Employees", len(all_employees))
    col2.metric("Shifts", len(all_shifts))
    
    if all_dates:
        st.caption(f"📅 Data: **{min(all_dates)}** → **{max(all_dates)}**")
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Shift legend
    st.markdown("##### 🎨 Shift Legend")
    for code in all_shifts:
        color = get_shift_color(code)
        timing = get_timing_str(code, shift_lookup)
        st.markdown(
            f'<span style="color:{color}; font-weight:600;">● {code}</span>'
            f'<span style="color:#94a3b8; font-size:0.8rem;"> — {timing}</span>',
            unsafe_allow_html=True
        )
    
    # Also show non-working codes
    for code, label in [("WO", "Week Off"), ("HO", "Holiday"), ("LEAVE", "Leave")]:
        color = get_shift_color(code)
        st.markdown(
            f'<span style="color:{color}; font-weight:600;">● {code}</span>'
            f'<span style="color:#94a3b8; font-size:0.8rem;"> — {label}</span>',
            unsafe_allow_html=True
        )
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Current time display
    st.markdown("##### 🕐 Current Time")
    st.markdown(
        f'<div style="font-size:1.5rem; font-weight:700; color:#818cf8;">'
        f'{datetime.now().strftime("%I:%M %p")}</div>'
        f'<div style="color:#94a3b8; font-size:0.85rem;">{today.strftime("%A, %B %d, %Y")}</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown(
    '<div class="hero-title">⚡ ShiftPulse — Workforce Manager</div>'
    '<div class="hero-subtitle">Real-time shift tracking, availability insights, and workforce analytics</div>',
    unsafe_allow_html=True
)
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Employee Lookup",
    "📅 Calendar View",
    "👥 Shift & Availability",
    "⚡ Real-Time Status",
    "📊 Analytics",
    "🧩 Smart Filter",
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — Employee Shift Lookup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab1:
    st.markdown('<div class="section-header">🔍 Employee Shift Lookup</div>', unsafe_allow_html=True)
    
    col_search, col_date = st.columns([3, 1])
    
    with col_search:
        selected_employee = st.selectbox(
            "Search Employee",
            options=[""] + all_employees,
            index=0,
            placeholder="Start typing to search...",
            key="emp_lookup"
        )
    
    with col_date:
        lookup_date = st.date_input("Date", value=today, key="lookup_date")
    
    if selected_employee:
        # Get shift for selected date
        emp_shift = shift_data[
            (shift_data["Associate Name"].str.upper() == selected_employee.upper()) &
            (shift_data["Date"] == lookup_date)
        ]
        
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        
        if not emp_shift.empty:
            row = emp_shift.iloc[0]
            shift_code = str(row["Shift Code"]).strip().upper()
            status = get_employee_status(shift_code)
            rt_status = classify_real_time(shift_code, shift_lookup, current_time)
            
            # Info cards
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👤 Employee", selected_employee)
            c2.metric("📋 Shift", shift_code if shift_code else "—")
            c3.metric("📌 Status", status)
            c4.metric("⚡ Right Now", rt_status)
            
            # Details
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("##### 📝 Employee Details")
                st.markdown(f"**Support Types:** {row.get('All Support Str', 'N/A')}")
                st.markdown(f"**Reporting To:** {row.get('Reporting Manager', 'N/A')}")
                st.markdown(f"**Location:** {row.get('Location', 'N/A')}")
                st.markdown(f"**Gender:** {row.get('Gender', 'N/A')}")
            
            with col_right:
                st.markdown("##### ⏰ Shift Timing")
                if shift_code in shift_lookup:
                    timing = shift_lookup[shift_code]
                    st.markdown(f"**Timing:** {get_timing_str(shift_code, shift_lookup)}")
                    st.markdown(f"**Start:** {timing['start_str']}")
                    st.markdown(f"**End:** {timing['end_str']}")
                    
                    # Visual timeline
                    start_h = timing["start"].hour + timing["start"].minute / 60
                    end_h = timing["end"].hour + timing["end"].minute / 60
                    color = get_shift_color(shift_code)
                    
                    if start_h < end_h:
                        left_pct = (start_h / 24) * 100
                        width_pct = ((end_h - start_h) / 24) * 100
                    else:
                        left_pct = (start_h / 24) * 100
                        width_pct = ((24 - start_h + end_h) / 24) * 100
                    
                    st.markdown(
                        f'<div style="position:relative; height:30px; background:rgba(30,30,55,0.8);'
                        f' border-radius:8px; margin-top:12px; overflow:hidden;">'
                        f'<div style="position:absolute; left:{left_pct}%; width:{min(width_pct, 100-left_pct)}%;'
                        f' height:100%; background:{color}; opacity:0.6; border-radius:8px;"></div>'
                        f'<div style="position:absolute; width:100%; text-align:center; line-height:30px;'
                        f' font-size:0.75rem; color:#e2e8f0; font-weight:600;">'
                        f'0h ─────────── 12h ─────────── 24h</div></div>',
                        unsafe_allow_html=True
                    )
                elif status in ("Leave", "Week Off", "Holiday"):
                    st.info(f"Employee is on **{status}** today.")
                else:
                    st.warning("Shift timing not defined for this code.")
        else:
            st.warning(f"No shift data found for **{selected_employee}** on **{lookup_date}**.")
    else:
        st.info("👆 Select an employee from the dropdown to view their shift details.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — Monthly Calendar View
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab2:
    st.markdown('<div class="section-header">📅 Monthly Shift Calendar</div>', unsafe_allow_html=True)
    
    col_emp, col_period = st.columns([3, 2])
    
    with col_emp:
        cal_employee = st.selectbox(
            "Select Employee",
            options=[""] + all_employees,
            index=0,
            placeholder="Choose an employee...",
            key="cal_emp"
        )
    
    # Determine available months/years from data
    if all_dates:
        available_months = sorted(set(
            (d.month, d.year) for d in all_dates if isinstance(d, date)
        ))
        if available_months:
            month_options = [f"{cal.month_name[m]} {y}" for m, y in available_months]
            default_idx = 0
            for i, (m, y) in enumerate(available_months):
                if m == today.month and y == today.year:
                    default_idx = i
                    break
            
            with col_period:
                selected_period = st.selectbox("Month", month_options, index=default_idx, key="cal_month_select")
                idx = month_options.index(selected_period)
                sel_month, sel_year = available_months[idx]
        else:
            sel_month, sel_year = today.month, today.year
    else:
        sel_month, sel_year = today.month, today.year
    
    if cal_employee:
        # Filter data for this employee and month
        emp_month_data = shift_data[
            (shift_data["Associate Name"].str.upper() == cal_employee.upper()) &
            (shift_data["Date"].apply(
                lambda d: d.month == sel_month and d.year == sel_year if isinstance(d, date) else False
            ))
        ]
        
        # Create a dict of day -> shift code
        day_shifts = {}
        for _, row in emp_month_data.iterrows():
            if isinstance(row["Date"], date):
                day_shifts[row["Date"].day] = str(row["Shift Code"]).strip().upper()
        
        # Build calendar
        st.markdown(f"### {cal.month_name[sel_month]} {sel_year} — {cal_employee}")
        
        days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        html = '<div class="cal-grid">'
        for d in days_header:
            html += f'<div class="cal-header">{d}</div>'
        
        first_day_weekday = cal.monthrange(sel_year, sel_month)[0]
        total_days = cal.monthrange(sel_year, sel_month)[1]
        
        # Empty cells before first day
        for _ in range(first_day_weekday):
            html += '<div class="cal-empty"></div>'
        
        # Day cells
        for day in range(1, total_days + 1):
            shift = day_shifts.get(day, "")
            color = get_shift_color(shift)
            bg = get_shift_bg(shift)
            is_today = (day == today.day and sel_month == today.month and sel_year == today.year)
            today_cls = " cal-today" if is_today else ""
            
            # Tooltip with timing
            tooltip = get_timing_str(shift, shift_lookup) if shift else ""
            if shift in ("WO", "HO", "LEAVE", "L"):
                tooltip = get_employee_status(shift)
            
            html += (
                f'<div class="cal-day{today_cls}" '
                f'style="background:{bg}; color:{color}; border-color:{color}33;" '
                f'title="{shift}: {tooltip}">'
                f'<span class="day-num">{day}</span>'
                f'<span class="shift-label">{shift if shift else "—"}</span>'
                f'</div>'
            )
        
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        
        # Summary stats
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        st.markdown("##### 📊 Monthly Summary")
        
        if day_shifts:
            shift_counts = pd.Series(list(day_shifts.values())).value_counts()
            summary_cols = st.columns(min(len(shift_counts), 7))
            for i, (code, count) in enumerate(shift_counts.items()):
                if i < len(summary_cols):
                    color = get_shift_color(code)
                    summary_cols[i].markdown(
                        f'<div style="text-align:center; padding:12px; background:rgba(22,22,40,0.85);'
                        f' border-radius:12px; border:1px solid {color}33;">'
                        f'<div style="font-size:1.8rem; font-weight:800; color:{color};">{count}</div>'
                        f'<div style="font-size:0.8rem; color:#94a3b8; font-weight:600;">{code} Days</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
    else:
        st.info("👆 Select an employee to view their monthly shift calendar.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — Shift-wise View + Availability
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab3:
    st.markdown('<div class="section-header">👥 Shift-wise View & Availability</div>', unsafe_allow_html=True)
    
    col_d, col_s, col_t = st.columns(3)
    
    with col_d:
        avail_date = st.date_input("Select Date", value=today, key="avail_date")
    
    with col_s:
        shift_filter = st.selectbox(
            "Filter by Shift",
            options=["All Shifts"] + all_shifts,
            key="shift_filter_3"
        )
    
    with col_t:
        support_filter = st.selectbox(
            "Filter by Support Type",
            options=["All Types"] + all_support_types,
            key="support_filter_3"
        )
    
    # Filter data
    day_data = shift_data[shift_data["Date"] == avail_date].copy()
    
    if shift_filter != "All Shifts":
        day_data = day_data[day_data["Shift Code"].str.upper() == shift_filter.upper()]
    
    if support_filter != "All Types":
        day_data = filter_by_support_type(day_data, support_filter)
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    if not day_data.empty:
        # ── Availability Summary (Feature #6) ──
        total = len(day_data)
        available_mask = day_data["Shift Code"].apply(is_available)
        available = day_data[available_mask]
        unavailable = day_data[~available_mask]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("👥 Total Employees", total)
        c2.metric("✅ Available", len(available),
                  delta=f"{len(available)/total*100:.0f}%" if total > 0 else "0%")
        c3.metric("🚫 Unavailable", len(unavailable),
                  delta=f"-{len(unavailable)}" if len(unavailable) > 0 else "0",
                  delta_color="inverse")
        
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.markdown("##### ✅ Available Employees")
            if not available.empty:
                display_df = available[["Associate Name", "Shift Code", "All Support Str", "Location"]].copy()
                display_df = display_df.rename(columns={"All Support Str": "Support Types"})
                display_df["Timing"] = display_df["Shift Code"].apply(
                    lambda c: get_timing_str(c, shift_lookup)
                )
                st.dataframe(
                    display_df.reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Associate Name": st.column_config.TextColumn("Employee", width="medium"),
                        "Shift Code": st.column_config.TextColumn("Shift", width="small"),
                        "Support Types": st.column_config.TextColumn("Support Types", width="large"),
                        "Location": st.column_config.TextColumn("Location", width="medium"),
                        "Timing": st.column_config.TextColumn("Timing", width="medium"),
                    }
                )
            else:
                st.info("No available employees for this filter.")
        
        with right_col:
            st.markdown("##### 🚫 Unavailable Employees")
            if not unavailable.empty:
                unavail_df = unavailable[["Associate Name", "Shift Code", "All Support Str", "Location"]].copy()
                unavail_df = unavail_df.rename(columns={"All Support Str": "Support Types"})
                unavail_df["Reason"] = unavail_df["Shift Code"].apply(get_employee_status)
                st.dataframe(
                    unavail_df[["Associate Name", "Reason", "Support Types", "Location"]].reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("Everyone is available! 🎉")
    else:
        st.warning(f"No data found for **{avail_date}** with the selected filters.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — Real-Time Availability
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab4:
    st.markdown('<div class="section-header">⚡ Real-Time Workforce Status</div>', unsafe_allow_html=True)
    
    now = datetime.now()
    st.markdown(
        f'<div style="font-size:1.2rem; color:#818cf8; font-weight:600; margin-bottom:16px;">'
        f'🕐 {now.strftime("%I:%M:%S %p")} — {now.strftime("%A, %B %d, %Y")}</div>',
        unsafe_allow_html=True
    )
    
    # Get today's data
    today_data = shift_data[shift_data["Date"] == today].copy()
    
    if not today_data.empty:
        # Classify each employee
        today_data["Real-Time Status"] = today_data["Shift Code"].apply(
            lambda c: classify_real_time(c, shift_lookup, current_time)
        )
        
        active = today_data[today_data["Real-Time Status"] == "Active Now"]
        upcoming = today_data[today_data["Real-Time Status"] == "Upcoming Shift"]
        off_duty = today_data[today_data["Real-Time Status"] == "Off Duty"]
        unknown = today_data[today_data["Real-Time Status"] == "Unknown Shift"]
        
        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🟢 Active Now", len(active))
        c2.metric("🟡 Upcoming", len(upcoming))
        c3.metric("⚪ Off Duty", len(off_duty))
        c4.metric("❓ Unknown", len(unknown))
        
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        
        # Active employees grid
        st.markdown("##### 🟢 Currently Active Employees")
        if not active.empty:
            cols = st.columns(3)
            for i, (_, row) in enumerate(active.iterrows()):
                sc = str(row["Shift Code"]).strip().upper()
                with cols[i % 3]:
                    color = get_shift_color(sc)
                    timing = get_timing_str(sc, shift_lookup)
                    support = row.get("All Support Str", "N/A")
                    location = row.get("Location", "N/A")
                    
                    st.markdown(
                        f'<div style="background:rgba(22,22,40,0.85); border:1px solid {color}44;'
                        f' border-radius:14px; padding:16px; margin-bottom:10px;'
                        f' border-left: 4px solid {color};">'
                        f'<div style="font-weight:700; color:#e2e8f0; font-size:0.95rem;">'
                        f'{row["Associate Name"]}</div>'
                        f'<div style="color:{color}; font-weight:600; font-size:0.85rem; margin-top:4px;">'
                        f'● Shift {sc} — {timing}</div>'
                        f'<div style="color:#94a3b8; font-size:0.78rem; margin-top:4px;">'
                        f'{support}</div>'
                        f'<div style="color:#64748b; font-size:0.75rem; margin-top:2px;">'
                        f'📍 {location}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        else:
            st.info("No employees are currently active.")
        
        # Upcoming shifts
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        st.markdown("##### 🟡 Upcoming Shifts")
        if not upcoming.empty:
            upcoming_display = upcoming[["Associate Name", "Shift Code", "All Support Str", "Location"]].copy()
            upcoming_display = upcoming_display.rename(columns={"All Support Str": "Support Types"})
            upcoming_display["Timing"] = upcoming_display["Shift Code"].apply(
                lambda c: get_timing_str(c, shift_lookup)
            )
            st.dataframe(
                upcoming_display.reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No upcoming shifts.")
        
        # Off duty
        with st.expander("⚪ Off Duty / Leave / Week Off Employees", expanded=False):
            if not off_duty.empty:
                off_display = off_duty[["Associate Name", "Shift Code", "All Support Str"]].copy()
                off_display = off_display.rename(columns={"All Support Str": "Support Types"})
                off_display["Reason"] = off_display["Shift Code"].apply(get_employee_status)
                st.dataframe(off_display.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.info("No off-duty employees.")
    else:
        st.warning("No shift data available for today.")
        if all_dates:
            st.info(f"Available dates: **{min(all_dates)}** to **{max(all_dates)}**")
            st.info("Select a different date using the other tabs to explore data.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5 — Analytics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab5:
    st.markdown('<div class="section-header">📊 Shift Distribution Analytics</div>', unsafe_allow_html=True)
    
    analytics_date = st.date_input("Select Date for Analytics", value=today, key="analytics_date")
    
    day_analytics = shift_data[shift_data["Date"] == analytics_date].copy()
    
    if not day_analytics.empty:
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        
        # Shift distribution
        shift_dist = day_analytics["Shift Code"].value_counts().reset_index()
        shift_dist.columns = ["Shift Code", "Count"]
        
        col_chart, col_table = st.columns([2, 1])
        
        with col_chart:
            st.markdown("##### 📊 Shift Distribution")
            colors = [get_shift_color(code) for code in shift_dist["Shift Code"]]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=shift_dist["Shift Code"],
                y=shift_dist["Count"],
                marker_color=colors,
                marker_line_width=0,
                text=shift_dist["Count"],
                textposition="outside",
                textfont=dict(size=14, color="#e2e8f0", family="Inter"),
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter"),
                xaxis=dict(title="Shift Code", gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="Employees", gridcolor="rgba(255,255,255,0.05)"),
                height=400,
                margin=dict(t=20, b=40, l=40, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_table:
            st.markdown("##### 📋 Summary Table")
            total = shift_dist["Count"].sum()
            shift_dist["Percentage"] = (shift_dist["Count"] / total * 100).round(1).astype(str) + "%"
            shift_dist["Timing"] = shift_dist["Shift Code"].apply(
                lambda c: get_timing_str(c, shift_lookup)
            )
            st.dataframe(
                shift_dist,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Shift Code": st.column_config.TextColumn("Shift", width="small"),
                    "Count": st.column_config.NumberColumn("Employees", width="small"),
                    "Percentage": st.column_config.TextColumn("%", width="small"),
                    "Timing": st.column_config.TextColumn("Timing", width="medium"),
                }
            )
        
        # Support type breakdown (using primary support type)
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        st.markdown("##### 🏢 Support Type × Shift Breakdown")
        
        if "Support Type" in day_analytics.columns:
            support_shift = day_analytics.groupby(
                ["Support Type", "Shift Code"]
            ).size().reset_index(name="Count")
            
            if not support_shift.empty and len(support_shift["Support Type"].unique()) > 1:
                fig2 = px.sunburst(
                    support_shift,
                    path=["Support Type", "Shift Code"],
                    values="Count",
                    color="Shift Code",
                    color_discrete_map={**SHIFT_COLORS},
                )
                fig2.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0", family="Inter"),
                    height=450,
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.dataframe(support_shift, use_container_width=True, hide_index=True)
        
        # Location breakdown
        if "Location" in day_analytics.columns:
            st.markdown("##### 📍 Availability by Location")
            avail_data = day_analytics[day_analytics["Shift Code"].apply(is_available)]
            if not avail_data.empty:
                loc_dist = avail_data.groupby("Location").size().reset_index(name="Available")
                
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(
                    x=loc_dist["Location"],
                    y=loc_dist["Available"],
                    marker_color="#818cf8",
                    marker_line_width=0,
                    text=loc_dist["Available"],
                    textposition="outside",
                    textfont=dict(size=13, color="#e2e8f0", family="Inter"),
                ))
                fig3.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8", family="Inter"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Available Employees"),
                    height=350,
                    margin=dict(t=20, b=40, l=40, r=20),
                )
                st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning(f"No data available for **{analytics_date}**.")
        if all_dates:
            st.info(f"Data available for: **{min(all_dates)}** to **{max(all_dates)}**")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 6 — Smart Filter
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab6:
    st.markdown('<div class="section-header">🧩 Smart Multi-Filter</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#94a3b8; font-size:0.9rem; margin-bottom:16px;">'
        'Combine multiple filters to find exactly who you need. '
        'Example: "All Application Support employees in G shift today in Chennai"</div>',
        unsafe_allow_html=True
    )
    
    f1, f2, f3, f4 = st.columns(4)
    
    with f1:
        smart_date = st.date_input("📅 Date", value=today, key="smart_date")
    
    with f2:
        smart_shift = st.multiselect(
            "🔄 Shift(s)",
            options=all_shifts,
            default=[],
            key="smart_shift",
            placeholder="Any shift..."
        )
    
    with f3:
        smart_support = st.multiselect(
            "🏢 Support Type(s)",
            options=all_support_types,
            default=[],
            key="smart_support",
            placeholder="Any type..."
        )
    
    with f4:
        smart_location = st.multiselect(
            "📍 Location(s)",
            options=[l for l in all_locations if l != "N/A"],
            default=[],
            key="smart_location",
            placeholder="Any location..."
        )
    
    only_available = st.toggle(
        "Show only available employees (exclude Leave/WO/HO)",
        value=True, key="smart_avail"
    )
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered = shift_data[shift_data["Date"] == smart_date].copy()
    
    if smart_shift:
        filtered = filtered[filtered["Shift Code"].str.upper().isin([s.upper() for s in smart_shift])]
    
    if smart_support:
        # Filter: employee must have at least one of the selected support types
        def has_any_support(types_list, selected):
            if not isinstance(types_list, list):
                return False
            return any(
                t.upper() in [s.upper() for s in selected]
                for t in types_list
            )
        filtered = filtered[filtered["All Support Types"].apply(
            lambda x: has_any_support(x, smart_support)
        )]
    
    if smart_location:
        filtered = filtered[filtered["Location"].str.upper().isin([l.upper() for l in smart_location])]
    
    if only_available:
        filtered = filtered[filtered["Shift Code"].apply(is_available)]
    
    # Build filter description
    filter_parts = [f"**{smart_date.strftime('%A, %b %d')}**"]
    if smart_shift:
        filter_parts.append(f"Shifts: {', '.join(smart_shift)}")
    if smart_support:
        filter_parts.append(f"Support: {', '.join(smart_support)}")
    if smart_location:
        filter_parts.append(f"Location: {', '.join(smart_location)}")
    
    st.markdown(f"🔎 Showing results for: {' | '.join(filter_parts)}")
    st.markdown(f"**{len(filtered)}** employee(s) found")
    
    if not filtered.empty:
        result_df = filtered[[
            "Associate Name", "Shift Code", "All Support Str",
            "Location", "Reporting Manager"
        ]].copy()
        result_df = result_df.rename(columns={"All Support Str": "Support Types"})
        
        result_df["Timing"] = result_df["Shift Code"].apply(
            lambda c: get_timing_str(c, shift_lookup)
        )
        result_df["Status"] = result_df["Shift Code"].apply(get_employee_status)
        result_df["Real-Time"] = result_df["Shift Code"].apply(
            lambda c: classify_real_time(c, shift_lookup, current_time)
        )
        
        st.dataframe(
            result_df.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Associate Name": st.column_config.TextColumn("Employee", width="medium"),
                "Shift Code": st.column_config.TextColumn("Shift", width="small"),
                "Support Types": st.column_config.TextColumn("Support Types", width="large"),
                "Location": st.column_config.TextColumn("Location", width="medium"),
                "Reporting Manager": st.column_config.TextColumn("Reports To", width="medium"),
                "Timing": st.column_config.TextColumn("Timing", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Real-Time": st.column_config.TextColumn("Now", width="small"),
            }
        )
        
        csv = result_df.to_csv(index=False)
        st.download_button(
            "📥 Download Results as CSV",
            data=csv,
            file_name=f"shift_filter_{smart_date.isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("No employees match the current filters. Try adjusting your criteria.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center; color:#475569; font-size:0.8rem; padding:16px 0;">'
    '⚡ ShiftPulse — Built with Streamlit | Data refreshes every 5 minutes'
    '</div>',
    unsafe_allow_html=True
)
