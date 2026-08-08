import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import time
import textwrap

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

API_BASE   = "http://127.0.0.1:8000/api"
API_QUERY  = f"{API_BASE}/query"
API_UPLOAD = f"{API_BASE}/upload"

PALETTE = ["#00F5D4", "#F72585", "#7209B7", "#3A0CA3", "#4CC9F0",
           "#FCA311", "#06D6A0", "#EF476F", "#118AB2", "#FFD166"]

st.set_page_config(
    page_title="DataWhisper.ai",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Global CSS — dark editorial aesthetic
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #050810 !important;
    color: #E8EAF0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #080D1A 0%, #070B16 100%) !important;
    border-right: 1px solid #17233F !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0.75rem 1rem 1rem 1rem !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: #0B1326 !important;
    border: 1px solid #1B3154 !important;
    border-radius: 12px !important;
    padding: 0.6rem !important;
    margin: 0.5rem 0 0.9rem 0 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #0D172B !important;
    border: 1px dashed #31517F !important;
    border-radius: 9px !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {
    color: #A0B4D0 !important;
}

/* Native sidebar collapse/expand control */
[data-testid="stSidebarCollapseButton"] button,
button[aria-label*="sidebar"],
button[aria-label*="Sidebar"] {
    color: #00F5D4 !important;
    background: #0C1428 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
}

[data-testid="stSidebarCollapseButton"] button:hover,
button[aria-label*="sidebar"]:hover,
button[aria-label*="Sidebar"]:hover {
    border-color: #00F5D4 !important;
    color: #00F5D4 !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #080D1A; }
::-webkit-scrollbar-thumb { background: #1E2D50; border-radius: 4px; }

/* ── Typography ── */
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; }

/* ── Hero Header ── */
.dw-hero {
    padding: 2.5rem 0 1.5rem 0;
    border-bottom: 1px solid #1A2340;
    margin-bottom: 2rem;
}
.dw-logo {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #00F5D4 0%, #4CC9F0 50%, #7209B7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}
.dw-tagline {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    color: #5E7090;
    margin-top: 0.4rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Cards ── */
.card {
    background: #0C1428;
    border: 1px solid #1A2340;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.card-accent {
    border-left: 3px solid #00F5D4;
}
.card-warn {
    border-left: 3px solid #F72585;
}
.card-purple {
    border-left: 3px solid #7209B7;
}

/* ── Section labels ── */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #00F5D4;
    margin-bottom: 0.5rem;
}

/* ── KPI tiles ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}
.kpi-tile {
    background: #0C1428;
    border: 1px solid #1A2340;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #00F5D4;
    line-height: 1;
}
.kpi-label {
    font-size: 0.72rem;
    color: #5E7090;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

/* ── Column type badges ── */
.badge {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
    font-size: 0.68rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.04em;
    margin: 2px;
}
.badge-numeric   { background: #0D2B3E; color: #4CC9F0; border: 1px solid #1A4A6E; }
.badge-category  { background: #1A0D2E; color: #B07FE8; border: 1px solid #3A1A5E; }
.badge-datetime  { background: #0D2E1A; color: #06D6A0; border: 1px solid #1A5E3A; }
.badge-text      { background: #2E1A0D; color: #FCA311; border: 1px solid #5E3A1A; }
.badge-id        { background: #2E0D1A; color: #EF476F; border: 1px solid #5E1A2E; }

/* ── Question pills ── */
.q-pill {
    display: inline-block;
    background: #0C1428;
    border: 1px solid #1E3060;
    border-radius: 20px;
    padding: 0.4rem 0.9rem;
    font-size: 0.82rem;
    color: #A0B4D0;
    margin: 0.25rem;
    cursor: pointer;
    transition: all 0.2s;
}
.q-pill:hover {
    border-color: #00F5D4;
    color: #00F5D4;
}

/* ── Sentiment bar ── */
.sent-bar-wrap { margin: 0.3rem 0; }
.sent-label { font-size: 0.72rem; color: #5E7090; margin-bottom: 2px; }
.sent-bar-bg {
    background: #1A2340;
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
}
.sent-bar-fill {
    height: 100%;
    border-radius: 4px;
}

/* ── SQL box ── */
.sql-box {
    background: #080D1A;
    border: 1px solid #1A2340;
    border-radius: 8px;
    padding: 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: #A0C4F0;
    white-space: pre-wrap;
    overflow-x: auto;
    line-height: 1.6;
}

/* ── Insight box ── */
.insight-box {
    background: linear-gradient(135deg, #0C1428 0%, #0D1E3A 100%);
    border: 1px solid #1E3060;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    font-size: 0.9rem;
    line-height: 1.65;
    color: #C0D4F0;
    position: relative;
}
.insight-box::before {
    content: '"';
    font-family: 'Syne', sans-serif;
    font-size: 3rem;
    color: #00F5D4;
    opacity: 0.3;
    position: absolute;
    top: -0.5rem;
    left: 0.5rem;
    line-height: 1;
}

/* ── Sidebar styles ── */
.sidebar-section {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #3A5080;
    padding: 0.5rem 0 0.25rem 0;
    border-top: 1px solid #1A2340;
    margin-top: 0.75rem;
}
.history-item {
    font-size: 0.8rem;
    color: #5E7090;
    padding: 0.3rem 0;
    border-bottom: 1px solid #0E1830;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.dot-green { background: #06D6A0; box-shadow: 0 0 6px #06D6A0; }
.dot-yellow { background: #FCA311; box-shadow: 0 0 6px #FCA311; }

/* ── Plotly override ── */
.js-plotly-plot .plotly { border-radius: 10px; }

/* ── Streamlit overrides ── */
[data-testid="stTextInput"] input {
    background: #0C1428 !important;
    border: 1px solid #1E3060 !important;
    border-radius: 8px !important;
    color: #E8EAF0 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.6rem 1rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #00F5D4 !important;
    box-shadow: 0 0 0 2px rgba(0,245,212,0.15) !important;
}

[data-testid="stButton"] button {
    background: linear-gradient(135deg, #00F5D4, #4CC9F0) !important;
    color: #050810 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] button:hover { opacity: 0.85 !important; }

[data-testid="stSelectbox"] select,
[data-testid="stSelectbox"] > div {
    background: #0C1428 !important;
    color: #E8EAF0 !important;
    border-color: #1E3060 !important;
}

.stDataFrame { border-radius: 10px; overflow: hidden; }
[data-testid="stDataFrame"] { background: #0C1428 !important; }

.stAlert { border-radius: 8px !important; }

/* ── Tab styling ── */
[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1A2340 !important;
    gap: 0 !important;
}
[data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    color: #5E7090 !important;
    border-radius: 0 !important;
    padding: 0.5rem 1rem !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #00F5D4 !important;
    border-bottom: 2px solid #00F5D4 !important;
    background: transparent !important;
}

/* ── Column profile table ── */
.prof-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.prof-table th {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #3A5080;
    padding: 0.5rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid #1A2340;
}
.prof-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #0E1830;
    color: #A0B4D0;
    vertical-align: top;
}
.prof-table tr:hover td { background: #0C1428; }
.null-high { color: #F72585; }
.null-mid  { color: #FCA311; }
.null-low  { color: #06D6A0; }

/* ── DataWhisper in-page panel: fixed/sticky presentation ── */
div[data-testid="stHorizontalBlock"]:has(.dw-panel-anchor) {
    align-items: flex-start !important;
}

div[data-testid="stHorizontalBlock"]:has(.dw-panel-anchor) > div[data-testid="column"]:first-child {
    position: sticky !important;
    top: 0.75rem !important;
    align-self: flex-start !important;
    height: calc(100vh - 1.5rem) !important;
    min-height: calc(100vh - 1.5rem) !important;
    overflow-y: auto !important;
    background: linear-gradient(180deg, #091225 0%, #070D1A 100%) !important;
    border: 1px solid #1A2A48 !important;
    border-radius: 14px !important;
    padding: 0.85rem !important;
    box-sizing: border-box !important;
    box-shadow: 0 16px 50px rgba(0,0,0,.20) !important;
}

div[data-testid="stHorizontalBlock"]:has(.dw-panel-anchor) > div[data-testid="column"]:first-child::-webkit-scrollbar {
    width: 4px;
}

div[data-testid="stHorizontalBlock"]:has(.dw-panel-anchor) > div[data-testid="column"]:first-child::-webkit-scrollbar-thumb {
    background: #1E3A5F;
    border-radius: 10px;
}

/* Prevent the panel from becoming visually empty when main content is long. */
.dw-panel-anchor {
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}


div[data-testid="stHorizontalBlock"]:has(.dw-collapsed-anchor) > div[data-testid="column"]:first-child {
    position: sticky !important;
    top: 0.75rem !important;
    align-self: flex-start !important;
    min-height: auto !important;
    height: auto !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
}

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────

defaults = {
    "dataset_loaded": False,
    "history": [],
    "profile": None,
    "table_name": None,
    "columns": [],
    "rows": 0,
    "last_result": None,
    "suggested_q": None,
    "active_query": "",
    "pending_suggested_query": None,
    "dashboard_charts": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def plotly_theme():
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#A0B4D0", size=12),
        xaxis=dict(gridcolor="#1A2340", linecolor="#1A2340", showgrid=True),
        yaxis=dict(gridcolor="#1A2340", linecolor="#1A2340", showgrid=True),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1A2340"),
        margin=dict(l=20, r=20, t=40, b=20),
    )


def render_chart(df: pd.DataFrame, chart: dict, key_suffix: str = ""):
    chart_type = chart.get("chart_type", "table")
    x = chart.get("x_axis")
    y_list = chart.get("y_axis", [])
    y = y_list[0] if y_list else None
    title = chart.get("title", "")
    palette = chart.get("color_palette", PALETTE)

    try:
        if chart_type == "number":
            col_name = y or (df.columns[0] if not df.empty else None)
            if col_name and col_name in df.columns:
                val = df[col_name].sum() if pd.api.types.is_numeric_dtype(df[col_name]) else df[col_name].iloc[0]
                val_str = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                st.markdown(f"""
                <div class="kpi-tile" style="text-align:center;padding:2rem;">
                    <div class="kpi-value">{val_str}</div>
                    <div class="kpi-label">{title}</div>
                </div>
                """, unsafe_allow_html=True)
            return

        if df.empty or x not in df.columns or y not in df.columns:
            st.dataframe(df, use_container_width=True)
            return

        if chart_type == "bar":
            fig = px.bar(df, x=x, y=y, title=title,
                         color_discrete_sequence=palette)
        elif chart_type == "line":
            fig = px.line(df, x=x, y=y, title=title,
                          color_discrete_sequence=palette, markers=True)
        elif chart_type == "area":
            fig = px.area(df, x=x, y=y, title=title,
                          color_discrete_sequence=palette)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x, y=y, title=title,
                             color_discrete_sequence=palette)
        elif chart_type == "pie":
            fig = px.pie(df, names=x, values=y, title=title,
                         color_discrete_sequence=palette)
        else:
            st.dataframe(df, use_container_width=True)
            return

        fig.update_layout(**plotly_theme())
        if chart_type != "pie":
            fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{key_suffix}")

    except Exception as e:
        st.dataframe(df, use_container_width=True)


def badge(label: str, kind: str) -> str:
    return f'<span class="badge badge-{kind}">{label}</span>'


def null_class(pct: float) -> str:
    if pct > 20:   return "null-high"
    if pct > 5:    return "null-mid"
    return "null-low"


def format_number(n) -> str:
    if n is None:
        return "—"
    try:
        f = float(n)
        if abs(f) >= 1_000_000:
            return f"{f/1_000_000:.1f}M"
        if abs(f) >= 1_000:
            return f"{f/1_000:.1f}K"
        return f"{f:,.2f}" if f != int(f) else f"{int(f):,}"
    except Exception:
        return str(n)


# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# In-page Dataset Panel
# ─────────────────────────────────────────────

if "data_panel_open" not in st.session_state:
    st.session_state.data_panel_open = True

if st.session_state.data_panel_open:
    panel_col, main_col = st.columns([1.18, 3.82], gap="medium")
else:
    panel_col, main_col = st.columns([0.20, 4.80], gap="medium")

with panel_col:

    if st.session_state.data_panel_open:

        st.markdown('<div class="dw-panel-anchor"></div>', unsafe_allow_html=True)

        top_left, top_right = st.columns([3.2, 0.7])

        with top_left:
            st.markdown("""
            <div style="padding:.25rem 0 .75rem 0;">
                <div style="
                    font-family:'Syne',sans-serif;
                    font-size:1.35rem;
                    font-weight:800;
                    color:#00F5D4;
                ">DataWhisper.ai</div>
                <div style="
                    font-size:.58rem;
                    color:#5E7090;
                    letter-spacing:.08em;
                    text-transform:uppercase;
                    margin-top:.15rem;
                ">Dataset Control Center</div>
            </div>
            """, unsafe_allow_html=True)

        with top_right:
            if st.button("‹", key="close_data_panel", help="Hide dataset panel"):
                st.session_state.data_panel_open = False
                st.rerun()

        st.markdown("""
        <div style="
            height:1px;
            background:#17233F;
            margin:.1rem 0 1rem 0;
        "></div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">Dataset</div>', unsafe_allow_html=True)

        st.markdown(
            '<div style="font-family:\'Syne\',sans-serif;font-size:1rem;font-weight:700;'
            'color:#E8EAF0;margin:0.4rem 0 0.45rem 0;">📂 Upload Dataset</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="font-size:0.75rem;color:#5E7090;margin-bottom:0.6rem;line-height:1.5;">'
            'Upload a CSV file to start profiling and querying your data.'
            '</div>',
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            label_visibility="visible",
            help="Supported format: CSV"
        )

        if uploaded_file:
            if st.button("⬆ Upload & Profile", use_container_width=True):
                with st.spinner("Uploading and profiling..."):
                    try:
                        # Reset position in case it was read already
                        uploaded_file.seek(0)
                        r = requests.post(API_UPLOAD, files={"file": uploaded_file}, timeout=120)
                        if r.status_code == 200:
                            resp = r.json()
                            if resp.get("success"):
                                d = resp["data"]
                                st.session_state.dataset_loaded = True
                                st.session_state.table_name    = d.get("table")
                                st.session_state.columns       = d.get("columns", [])
                                st.session_state.rows          = d.get("rows", 0)
                                st.session_state.profile       = d.get("profile", {})
                                st.session_state.last_result   = None
                                st.session_state.history       = []

                                # Suggested questions from profiler
                                profile = st.session_state.profile or {}
                                st.session_state.suggested_q = profile.get("suggested_questions", [])

                                st.success("Ready")
                            else:
                                st.error(resp.get("error", "Upload failed"))
                        else:
                            st.error(f"Server error {r.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend not reachable")

        # Status
        st.markdown('<div class="sidebar-section">Status</div>', unsafe_allow_html=True)
        if st.session_state.dataset_loaded:
            st.markdown(f"""
            <div style="font-size:0.8rem;color:#5E7090;line-height:1.8;">
                <span class="status-dot dot-green"></span><b style="color:#E8EAF0;">{st.session_state.table_name}</b><br>
                <span style="padding-left:14px;">{st.session_state.rows:,} rows · {len(st.session_state.columns)} cols</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="font-size:0.8rem;color:#5E7090;">
                <span class="status-dot dot-yellow"></span>No dataset loaded
            </div>
            """, unsafe_allow_html=True)

        # History
        if st.session_state.history:
            st.markdown('<div class="sidebar-section">Recent Queries</div>', unsafe_allow_html=True)
            for q in reversed(st.session_state.history[-8:]):
                st.markdown(f'<div class="history-item">› {q}</div>', unsafe_allow_html=True)

        # Clear
        if st.session_state.dataset_loaded:
            st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
            if st.button("🗑 Clear Session", use_container_width=True):
                for k, v in defaults.items():
                    st.session_state[k] = v
                st.rerun()


        # Product features moved from the bottom of the page into the panel.
        st.markdown("""
        <div style="
            height:1px;
            background:#17233F;
            margin:1.15rem 0 .9rem 0;
        "></div>
        <div style="
            font-family:'Syne',sans-serif;
            font-size:.68rem;
            font-weight:700;
            color:#5E7090;
            letter-spacing:.18em;
            text-transform:uppercase;
            margin-bottom:.65rem;
        ">Features</div>
        """, unsafe_allow_html=True)

        sidebar_features = [
            ("🔎", "Smart Profiling", "Column types, nulls, duplicates and data quality."),
            ("💬", "Natural Language", "Ask questions about your dataset in plain English."),
            ("⚡", "SQL Generation", "AI converts your question into executable SQL."),
            ("📊", "Charts & Insights", "Automatically visualize results and explain them."),
        ]

        for icon, title, description in sidebar_features:
            st.markdown(f"""
            <div style="
                background:#0A1325;
                border:1px solid #182B48;
                border-radius:10px;
                padding:.65rem .7rem;
                margin:.4rem 0;
            ">
                <div style="
                    font-size:.92rem;
                    margin-bottom:.2rem;
                    color:#E8EAF0;
                ">
                    {icon}
                    <span style="
                        font-family:'Syne',sans-serif;
                        font-size:.72rem;
                        font-weight:700;
                        margin-left:.2rem;
                    ">{title}</span>
                </div>
                <div style="
                    font-size:.61rem;
                    line-height:1.4;
                    color:#5E7090;
                ">{description}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            margin-top:1.1rem;
            padding-top:.8rem;
            border-top:1px solid #17233F;
            text-align:center;
            font-size:.67rem;
            color:#5E7090;
        ">
            Developed by <span style="color:#00F5D4;font-weight:700;">Arpit Singh</span>
        </div>
        """, unsafe_allow_html=True)

    else:

        st.markdown('<div class="dw-collapsed-anchor"></div>', unsafe_allow_html=True)

        if st.button("›", key="open_data_panel", help="Open dataset panel"):
            st.session_state.data_panel_open = True
            st.rerun()

with main_col:
    # ─────────────────────────────────────────────
    # Hero
    # ─────────────────────────────────────────────

    st.markdown("""
    <div class="dw-hero">
        <div class="dw-logo">DataWhisper.ai</div>
        <div class="dw-tagline">Natural Language · SQL · Charts · Insights — All in one place</div>
    </div>
    """, unsafe_allow_html=True)


    # ─────────────────────────────────────────────
    # No dataset state
    # ─────────────────────────────────────────────

    if not st.session_state.dataset_loaded:

        # Professional welcome / onboarding screen.
        welcome_html = """
        <div class="card" style="
            text-align:center;
            padding:4.5rem 2rem 3.5rem 2rem;
            background:radial-gradient(circle at 50% 0%, rgba(0,245,212,0.08), transparent 38%), #0C1428;
            border:1px solid #1B3154;
            border-radius:14px;
            box-shadow:0 18px 60px rgba(0,0,0,0.18);
        ">
            <div style="
                width:72px;height:72px;margin:0 auto 1.3rem auto;
                border-radius:20px;display:flex;align-items:center;justify-content:center;
                background:linear-gradient(135deg,#0D2B3E,#10243F);
                border:1px solid #21496B;font-size:2.6rem;
            ">🌊</div>

            <div style="
                font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;
                letter-spacing:-0.04em;margin-bottom:0.65rem;color:#E8EAF0;
            ">Turn Data Into Answers</div>

            <div style="
                color:#7183A8;font-size:0.95rem;max-width:560px;
                margin:0 auto;line-height:1.7;
            ">
                Upload your CSV from the <b style="color:#00F5D4;">Dataset panel</b>
                to automatically profile your data, generate insights,
                suggest questions, write SQL, and visualize the results.
            </div>

            <div style="
                margin:2rem auto 0 auto;max-width:650px;height:1px;
                background:linear-gradient(90deg,transparent,#1E3060,transparent);
            "></div>
        </div>
        """

        # st.html renders the HTML directly instead of passing it through
        # Markdown, which fixes the literal <div style="..."> problem.
        if hasattr(st, "html"):
            st.html(welcome_html)
        else:
            st.markdown(welcome_html, unsafe_allow_html=True)

        st.stop()


    # ─────────────────────────────────────────────
    # Tabs
    # ─────────────────────────────────────────────

    tab_query, tab_profile, tab_dashboard = st.tabs([
        "💬  QUERY",
        "🔬  DATA PROFILE",
        "📊  AUTO DASHBOARD",
    ])


    # ═══════════════════════════════════════════════════════════
    # TAB 1 — QUERY
    # ═══════════════════════════════════════════════════════════

    with tab_query:

        # ── Suggested questions ──────────────────────────────────
        # ─────────────────────────────────────────────
    # Suggested Questions (Improved UI)
    # ─────────────────────────────────────────────

        if "selected_question" not in st.session_state:
            st.session_state.selected_question = ""

        if st.session_state.suggested_q:

            st.markdown(
                '<div class="section-label">💡 Suggested Questions</div>',
                unsafe_allow_html=True
            )

            cols_q = st.columns(2)

            icons = [
                "📈", "📊", "🏆", "💰", "🌍",
                "📅", "👥", "📦", "🔥", "⭐"
            ]

            for i, q in enumerate(st.session_state.suggested_q[:10]):

                with cols_q[i % 2]:

                    selected = q == st.session_state.selected_question

                    if st.button(
                        f"{icons[i]}  {q}",
                        key=f"sq_{i}",
                        use_container_width=True,
                        type="primary" if selected else "secondary"
                    ):

                        st.session_state.selected_question = q
                        st.session_state.active_query = q
                        st.session_state.query_input_box = q

                        # Mark this suggestion for immediate execution after rerun.
                        st.session_state.pending_suggested_query = q

                        st.rerun()

        st.markdown("---")

        # ── Query input ──────────────────────────────────────────
        st.markdown('<div class="section-label">Ask Your Data</div>', unsafe_allow_html=True)

        query_input = st.text_input(
            "Query",
            value=st.session_state.active_query,
            placeholder="Ask anything about your data...",
            label_visibility="collapsed",
            key="query_input_box",
        )

        if st.session_state.selected_question:
            st.info(f"💡 Selected Suggestion: {st.session_state.selected_question}")

        run_col, clear_col = st.columns([1, 5])
        with run_col:
            run_btn = st.button("▶ Run", use_container_width=True)
        with clear_col:
            if st.button("✕ Clear", use_container_width=True):
                st.session_state.active_query = ""
                st.session_state.last_result  = None
                st.rerun()

        # ── Execute ───────────────────────────────────────────────
        # A suggested question is executed automatically after its button is clicked.
        # The normal user-entered query + Run button flow remains unchanged.
        pending_suggested_query = st.session_state.get("pending_suggested_query")
        execute_query = bool(run_btn or pending_suggested_query)

        if execute_query and (query_input or pending_suggested_query):
            if pending_suggested_query:
                query_input = pending_suggested_query
                st.session_state.active_query = query_input
                st.session_state.pending_suggested_query = None
            else:
                st.session_state.active_query = query_input

            # Build conversation context
            prev_q = st.session_state.history[-1] if st.session_state.history else None
            prev_sql = (
                st.session_state.last_result.get("generated_sql")
                if st.session_state.last_result else None
            )

            payload = {"query": query_input}
            if prev_q:   payload["previous_query"] = prev_q
            if prev_sql: payload["previous_sql"]   = prev_sql

            with st.spinner("Thinking..."):
                try:
                    t0 = time.time()
                    response = requests.post(API_QUERY, json=payload, timeout=90)
                    elapsed = round(time.time() - t0, 2)
                except requests.exceptions.ConnectionError:
                    st.error("Backend not reachable — is uvicorn running?")
                    st.stop()

            if response.status_code != 200:
                st.error(f"Backend error {response.status_code}")
                st.stop()

            result = response.json()
            if not result.get("success"):
                st.error(result.get("error", "Query failed"))
                st.stop()

            data       = result["data"].get("data", [])
            chart_info = result["data"].get("chart_info", {})
            sql        = result["data"].get("generated_sql", "")
            insight    = result["data"].get("insight", "")

            st.session_state.last_result = result["data"]
            st.session_state.history.append(query_input)

            df = pd.DataFrame(data)

            # ── Results layout ────────────────────────────────────
            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#3A5080;margin:1rem 0 0.5rem 0;">
                {len(df)} rows returned · {elapsed}s
            </div>
            """, unsafe_allow_html=True)

            left, right = st.columns([3, 2])

            with left:
                st.markdown('<div class="section-label">Visualization</div>', unsafe_allow_html=True)
                with st.container():
                    render_chart(df, chart_info, key_suffix="query")

            with right:
                st.markdown('<div class="section-label">AI Insight</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

                st.markdown('<div class="section-label" style="margin-top:1rem;">Generated SQL</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)

                if result["data"].get("repaired"):
                    fixed_sql = result["data"].get("fixed_sql", "")
                    st.markdown('<div class="section-label" style="margin-top:1rem;color:#FCA311;">Auto-Repaired SQL</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="sql-box" style="border-color:#FCA311;">{fixed_sql}</div>', unsafe_allow_html=True)

            # ── Raw data table ────────────────────────────────────
            with st.expander("📋 Raw Data", expanded=False):
                st.dataframe(df, use_container_width=True)


    # ═══════════════════════════════════════════════════════════
    # TAB 2 — DATA PROFILE
    # ═══════════════════════════════════════════════════════════

    with tab_profile:
        profile = st.session_state.profile or {}

        if not profile:
            st.info("Profile not available — re-upload your dataset.")
            st.stop()

        summary  = profile.get("summary", {})
        col_prof = profile.get("column_profiles", [])
        sentiment = profile.get("sentiment", {})
        description = profile.get("description", "")

        # ── Description ───────────────────────────────────────────
        if description:
            st.markdown('<div class="section-label">About This Dataset</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="insight-box">{description}</div>', unsafe_allow_html=True)
            st.markdown("")

        # ── KPI tiles ────────────────────────────────────────────
        st.markdown('<div class="section-label">Dataset Overview</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-tile">
                <div class="kpi-value">{format_number(summary.get('total_rows'))}</div>
                <div class="kpi-label">Total Rows</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-value">{summary.get('total_columns', 0)}</div>
                <div class="kpi-label">Columns</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-value">{summary.get('numeric_column_count', 0)}</div>
                <div class="kpi-label">Numeric</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-value">{summary.get('categorical_column_count', 0)}</div>
                <div class="kpi-label">Categorical</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-value">{summary.get('datetime_column_count', 0)}</div>
                <div class="kpi-label">Datetime</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-value">{summary.get('duplicate_rows', 0)}</div>
                <div class="kpi-label">Duplicates</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-value">{format_number(summary.get('memory_kb'))} KB</div>
                <div class="kpi-label">Memory</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Column type breakdown ─────────────────────────────────
        type_map = {
            "numeric":     ("Numeric",     "numeric"),
            "categorical": ("Categorical", "category"),
            "datetime":    ("Datetime",    "datetime"),
            "text":        ("Text",        "text"),
            "identifier":  ("ID",          "id"),
        }

        left_col, right_col = st.columns([3, 2])

        with left_col:
            # ── Column profiles table ─────────────────────────────
            st.markdown('<div class="section-label">Column Profiles</div>', unsafe_allow_html=True)

            # Build a clean DataFrame for the column profile table
            # (Streamlit strips <table> from unsafe_allow_html — use st.dataframe instead)
            profile_rows = []
            for p in col_prof:
                sem = p.get("semantic_type", "other")
                null_pct = p.get("null_pct", 0)

                extras = []
                if sem == "numeric":
                    extras.append(
                        f"min {format_number(p.get('min'))} · "
                        f"max {format_number(p.get('max'))} · "
                        f"mean {format_number(p.get('mean'))}"
                    )
                elif "top_values" in p:
                    top = ", ".join(t["value"] for t in p["top_values"][:3])
                    extras.append(f"Top: {top}")
                if sem == "datetime":
                    extras.append(f"{p.get('min_date','')} → {p.get('max_date','')}")

                profile_rows.append({
                    "Column":    p["column"],
                    "Type":      sem,
                    "Dtype":     p.get("dtype", ""),
                    "Unique":    f"{p.get('unique_count', 0):,}",
                    "Nulls %":   f"{null_pct}%",
                    "Stats / Top Values": " | ".join(extras) if extras else "—",
                })

            profile_df = pd.DataFrame(profile_rows)

            # Colour-code the Nulls % column via pandas Styler
            def colour_null(val):
                pct = float(val.replace("%", "")) if val != "—" else 0
                if pct > 20:   return "color: #F72585"
                if pct > 5:    return "color: #FCA311"
                return "color: #06D6A0"

            styled = (
                profile_df.style
                .applymap(colour_null, subset=["Nulls %"])
                .set_properties(**{"background-color": "#0C1428", "color": "#A0B4D0",
                                   "border": "1px solid #1A2340"})
                .set_table_styles([
                    {"selector": "th", "props": [
                        ("background-color", "#080D1A"),
                        ("color", "#3A5080"),
                        ("font-family", "DM Mono, monospace"),
                        ("font-size", "0.7rem"),
                        ("letter-spacing", "0.1em"),
                        ("text-transform", "uppercase"),
                        ("border", "1px solid #1A2340"),
                    ]},
                ])
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)

        with right_col:
            # ── Data quality ──────────────────────────────────────
            st.markdown('<div class="section-label">Data Quality</div>', unsafe_allow_html=True)
            dup_pct = summary.get("duplicate_pct", 0)
            cols_nulls = summary.get("columns_with_nulls", [])

            quality_score = max(0, 100 - dup_pct - len(cols_nulls) * 3)
            q_color = "#06D6A0" if quality_score >= 80 else "#FCA311" if quality_score >= 50 else "#F72585"

            st.markdown(f"""
            <div class="card card-accent">
                <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
                    <div style="font-family:'Syne',sans-serif;font-size:2.5rem;font-weight:800;color:{q_color};">
                        {quality_score:.0f}
                    </div>
                    <div>
                        <div style="font-size:0.8rem;color:#E8EAF0;font-weight:500;">Quality Score</div>
                        <div style="font-size:0.72rem;color:#5E7090;">out of 100</div>
                    </div>
                </div>
                <div style="font-size:0.8rem;color:#5E7090;line-height:2;">
                    Duplicate rows: <b style="color:#E8EAF0;">{summary.get('duplicate_rows',0):,} ({dup_pct}%)</b><br>
                    Cols with nulls: <b style="color:#E8EAF0;">{len(cols_nulls)}</b><br>
                    Fully unique cols: <b style="color:#E8EAF0;">{len(summary.get('fully_unique_columns',[]))}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Sentiment ─────────────────────────────────────────
            if sentiment:
                st.markdown('<div class="section-label" style="margin-top:1rem;">Sentiment Analysis</div>', unsafe_allow_html=True)
                for col_name, sent in sentiment.items():
                    pos_pct = sent.get("positive_pct", 0)
                    neg_pct = sent.get("negative_pct", 0)
                    neu_pct = sent.get("neutral_pct",  0)
                    st.markdown(f"""
                    <div class="card">
                        <div style="font-size:0.8rem;color:#E8EAF0;margin-bottom:0.6rem;font-weight:500;">{col_name}</div>
                        <div class="sent-bar-wrap">
                            <div class="sent-label">Positive · {pos_pct}%</div>
                            <div class="sent-bar-bg">
                                <div class="sent-bar-fill" style="width:{pos_pct}%;background:#06D6A0;"></div>
                            </div>
                        </div>
                        <div class="sent-bar-wrap">
                            <div class="sent-label">Negative · {neg_pct}%</div>
                            <div class="sent-bar-bg">
                                <div class="sent-bar-fill" style="width:{neg_pct}%;background:#F72585;"></div>
                            </div>
                        </div>
                        <div class="sent-bar-wrap">
                            <div class="sent-label">Neutral · {neu_pct}%</div>
                            <div class="sent-bar-bg">
                                <div class="sent-bar-fill" style="width:{neu_pct}%;background:#4CC9F0;"></div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── Nulls chart ───────────────────────────────────────
            if cols_nulls:
                st.markdown('<div class="section-label" style="margin-top:1rem;">Null % by Column</div>', unsafe_allow_html=True)
                null_data = {
                    p["column"]: p["null_pct"]
                    for p in col_prof if p["null_pct"] > 0
                }
                if null_data:
                    fig = px.bar(
                        x=list(null_data.values()),
                        y=list(null_data.keys()),
                        orientation="h",
                        color=list(null_data.values()),
                        color_continuous_scale=["#06D6A0", "#FCA311", "#F72585"],
                    )
                    _t1 = plotly_theme(); _t1['margin'] = dict(l=0, r=0, t=10, b=0)
                    fig.update_layout(**_t1, height=200, showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig, use_container_width=True)


    # ═══════════════════════════════════════════════════════════
    # TAB 3 — AUTO DASHBOARD
    # ═══════════════════════════════════════════════════════════

    with tab_dashboard:

        profile = st.session_state.profile or {}
        col_prof = profile.get("column_profiles", [])

        if not col_prof:
            st.info("Upload a dataset to auto-generate the dashboard.")
            st.stop()

        st.markdown('<div class="section-label">Auto-Generated Dashboard</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.82rem;color:#5E7090;margin-bottom:1.5rem;">
            DataWhisper automatically detects column types and builds the most
            meaningful charts for your data — no queries needed.
        </div>
        """, unsafe_allow_html=True)

        # ── Fetch dashboard charts from backend ───────────────────
        if st.button("🔄 Generate / Refresh Dashboard", use_container_width=False):
            with st.spinner("Building dashboard..."):
                try:
                    r = requests.post(
                        f"{API_BASE}/dashboard",
                        json={"table": st.session_state.table_name},
                        timeout=120,
                    )
                    if r.status_code == 200:
                        resp = r.json()
                        if resp.get("success"):
                            st.session_state.dashboard_charts = resp["data"].get("charts", [])
                        else:
                            st.error(resp.get("error", "Dashboard generation failed"))
                    else:
                        st.warning(f"Dashboard endpoint returned {r.status_code} — showing profile-based fallback.")
                except Exception as e:
                    st.warning(f"Could not reach dashboard endpoint: {e}")

        # ── Render charts ────────────────────────────────────────
        charts = st.session_state.dashboard_charts

        if charts:
            # Render in 2-column grid
            for i in range(0, len(charts), 2):
                cols = st.columns(2)
                for j, chart_def in enumerate(charts[i:i+2]):
                    with cols[j]:
                        st.markdown(f"""
                        <div class="card" style="margin-bottom:0.5rem;">
                            <div class="section-label">{chart_def.get('title','Chart')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Fetch data for this chart via query
                        q_for_chart = chart_def.get("title", "")
                        if q_for_chart:
                            try:
                                resp = requests.post(
                                    API_QUERY,
                                    json={"query": q_for_chart},
                                    timeout=60,
                                )
                                if resp.status_code == 200 and resp.json().get("success"):
                                    rows_data = resp.json()["data"].get("data", [])
                                    chart_df  = pd.DataFrame(rows_data)
                                    render_chart(chart_df, chart_def, key_suffix=f"dash_{i}_{j}")

                                    insight = chart_def.get("insight", "")
                                    if insight:
                                        st.markdown(f"""
                                        <div style="font-size:0.78rem;color:#5E7090;padding:0.5rem 0.25rem;">
                                            💡 {insight}
                                        </div>
                                        """, unsafe_allow_html=True)
                            except Exception:
                                st.markdown(f'<div class="card"><em style="color:#5E7090;">Could not load data for this chart.</em></div>', unsafe_allow_html=True)

        else:
            # ── Fallback: profile-based static summary ────────────
            st.markdown('<div class="section-label">Column Distribution Overview</div>', unsafe_allow_html=True)

            numeric_profiles = [p for p in col_prof if p.get("semantic_type") == "numeric"]
            cat_profiles     = [p for p in col_prof if p.get("semantic_type") == "categorical"]

            if numeric_profiles:
                st.markdown('<div class="section-label" style="margin-top:1rem;">Numeric Column Ranges</div>', unsafe_allow_html=True)
                range_data = [{
                    "Column": p["column"],
                    "Min":    p.get("min", 0),
                    "Mean":   p.get("mean", 0),
                    "Max":    p.get("max", 0),
                } for p in numeric_profiles if p.get("max") is not None]

                if range_data:
                    range_df = pd.DataFrame(range_data)
                    fig = go.Figure()
                    for _, row in range_df.iterrows():
                        fig.add_trace(go.Bar(
                            name=row["Column"],
                            x=[row["Column"]],
                            y=[row["Max"]],
                            marker_color=PALETTE[_ % len(PALETTE)],
                            showlegend=False,
                        ))
                    fig.update_layout(**plotly_theme(), title="Max values per numeric column", height=280)
                    st.plotly_chart(fig, use_container_width=True)

            if cat_profiles:
                cols_cat = st.columns(min(3, len(cat_profiles)))
                for i, p in enumerate(cat_profiles[:3]):
                    with cols_cat[i]:
                        top_vals = p.get("top_values", [])
                        if top_vals:
                            tv_df = pd.DataFrame(top_vals)
                            fig = px.pie(
                                tv_df, names="value", values="count",
                                title=p["column"].replace("_", " ").title(),
                                color_discrete_sequence=PALETTE,
                            )
                            _t2 = plotly_theme(); _t2['margin'] = dict(l=10, r=10, t=40, b=10)
                            fig.update_layout(**_t2, height=250)
                            st.plotly_chart(fig, use_container_width=True)

            st.markdown("""
            <div class="card" style="text-align:center;padding:1.5rem;margin-top:1rem;">
                <div style="color:#5E7090;font-size:0.85rem;">
                    Click <b style="color:#00F5D4;">Generate / Refresh Dashboard</b> above to load
                    AI-generated charts that query your actual data.
                </div>
            </div>
            """, unsafe_allow_html=True)