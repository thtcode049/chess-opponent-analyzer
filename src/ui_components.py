"""
UI Components & Design System Helper Module
-------------------------------------------
Chức năng: Cung cấp hệ thống UI Component dùng chung (Global Design System)
chuẩn hóa theo phong cách "Chess Opponent Analyzer — Modern Light Chess Analytics".
"""

import os
import base64
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from src.i18n import t

_ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons"))

# Global Semantic & Brand Design Tokens
COLOR_WIN = "#22C55E"          # Victory Green
COLOR_DRAW = "#94A3B8"         # Cool Gray Draw
COLOR_LOSS = "#EF4444"         # Coral Red Loss
COLOR_WARNING = "#F59E0B"      # Amber Warning
COLOR_PRIMARY = "#10B981"      # Emerald Primary Brand Color
COLOR_PRIMARY_HOVER = "#059669"
COLOR_BLUE = "#3B82F6"         # Analytics Blue Accent
COLOR_TEXT_PRIMARY = "#0F172A"
COLOR_TEXT_SECONDARY = "#475569"
COLOR_TEXT_MUTED = "#94A3B8"
COLOR_BORDER = "#E2E8F0"
COLOR_BG_PAGE = "#F5F7FA"
COLOR_BG_SURFACE = "#FFFFFF"


def apply_global_styles(theme_mode: str = "light"):
    """Tải và áp dụng Global Light Chess Analytics Design System CSS."""
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains-Mono:wght@500;600;700&display=swap');

        :root {
            --bg-page: #F5F7FA;
            --bg-primary: #FFFFFF;
            --bg-surface: #FFFFFF;
            --bg-soft: #F0F4F8;
            --bg-hover: #E8EEF5;

            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #94A3B8;

            --primary: #10B981;
            --primary-hover: #059669;

            --blue: #3B82F6;
            --blue-soft: #EFF6FF;

            --chess-dark: #1E293B;
            --chess-light: #F8FAFC;

            --win: #22C55E;
            --draw: #94A3B8;
            --loss: #EF4444;
            --warning: #F59E0B;

            --border: #E2E8F0;
            --border-strong: #CBD5E1;

            --shadow-sm: 0 1px 3px rgba(15,23,42,.08);
            --shadow-md: 0 6px 20px rgba(15,23,42,.08);
        }

        .stApp, body {
            background-color: var(--bg-page) !important;
            color: var(--text-primary) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Typography */
        h1, h2, h3 {
            color: var(--text-primary) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
        }
        
        .mono-font, code, pre, div.stCode, .pgn-text, .fen-text {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* Content Container - Margins aligned with sidebar layout */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            max-width: 1440px !important;
            margin-left: 0 !important;
            margin-right: auto !important;
        }

        /* Rationale: Hide default Streamlit top toolbar, deploy button, header decoration, and hamburger/collapse controls to maintain a clean desktop app layout. */
        [data-testid="stAppDeployButton"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
            width: 0px !important;
        }

        /* Rationale: Remove top header padding to maximize vertical space. */
        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0px !important;
            min-height: 0px !important;
            padding: 0 !important;
        }

        /* Rationale: Style fixed permanent 250px left sidebar navigation. Streamlit sidebar by default is collapsible with dynamic width. */
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"][aria-expanded="false"],
        section[data-testid="stSidebar"][aria-expanded="true"] {
            display: flex !important;
            visibility: visible !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;
            height: 100vh !important;
            width: 250px !important;
            min-width: 250px !important;
            max-width: 250px !important;
            margin-left: 0 !important;
            transform: none !important;
            z-index: 100 !important;
            background-color: #FFFFFF !important;
            border-right: 1px solid var(--border) !important;
        }

        /* Rationale: Offset main app section by 250px to accommodate the fixed left sidebar. */
        [data-testid="stMain"],
        section[data-testid="stMain"],
        div[data-testid="stAppViewContainer"] > section.main,
        div[data-testid="stAppViewContainer"] > section[data-testid="stMain"],
        .main,
        .stMain {
            margin-left: 250px !important;
            padding-left: 0rem !important;
            width: calc(100% - 250px) !important;
            box-sizing: border-box !important;
        }

        /* Rationale: Collapse empty Streamlit sidebar header container to prevent giant top space. */
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
        div[data-testid="stSidebarHeader"] {
            display: none !important;
            height: 0px !important;
            min-height: 0px !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Rationale: Sidebar content top padding. */
        div[data-testid="stSidebarUserContent"],
        div[data-testid="stSidebarContent"],
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding-top: 0.75rem !important;
            padding-bottom: 0.75rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            overflow-y: auto !important;
        }



        /* Rationale: Tighten spacing between sidebar element containers to fit all buttons cleanly. */
        div[data-testid="stSidebar"] div.stElementContainer,
        div[data-testid="stSidebar"] div.element-container {
            margin-bottom: 2px !important;
        }

        /* Rationale: Hide sidebar scrollbars for clean navigation appearance. */
        section[data-testid="stSidebar"] ::-webkit-scrollbar,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] ::-webkit-scrollbar {
            display: none !important;
            width: 0px !important;
            height: 0px !important;
        }

        .sidebar-nav-group {
            font-size: 9.5px;
            font-weight: 800;
            letter-spacing: 0.7px;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-top: 8px;
            margin-bottom: 2px;
        }

        /* Rationale: Custom compact button sizing for sidebar navigation links. */
        div[data-testid="stSidebar"] div.stButton button {
            width: 100% !important;
            justify-content: flex-start !important;
            background-color: transparent !important;
            border: 1px solid transparent !important;
            color: var(--text-secondary) !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
            padding: 3px 8px !important;
            border-radius: 6px !important;
            height: 30px !important;
            min-height: 30px !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
            margin-bottom: 1px !important;
        }

        /* Rationale: Compact selectbox sizing inside sidebar. */
        div[data-testid="stSidebar"] div[data-baseweb="select"] {
            min-height: 30px !important;
        }
        div[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            min-height: 30px !important;
            padding-top: 1px !important;
            padding-bottom: 1px !important;
        }

        div[data-testid="stSidebar"] div.stButton button:hover {
            background-color: var(--bg-soft) !important;
            color: var(--text-primary) !important;
            border-color: var(--border) !important;
        }

        /* Rationale: Highlight active sidebar button when selected. */
        div[data-testid="stSidebar"] div.stButton button[kind="primary"],
        div[data-testid="stSidebar"] div.stButton button[data-testid="stBaseButton-primary"] {
            background-color: #ECFDF5 !important;
            color: #059669 !important;
            border: 1px solid #A7F3D0 !important;
            font-weight: 700 !important;
        }

        div[data-testid="stSidebar"] div.stButton button[kind="primary"] *,
        div[data-testid="stSidebar"] div.stButton button[data-testid="stBaseButton-primary"] * {
            color: #059669 !important;
            font-weight: 700 !important;
        }

        /* Rationale: General button styling for modern light theme aesthetics across the app. */
        .stButton button, 
        button[data-testid="stBaseButton-secondary"],
        button[data-testid="stBaseButton-primary"] {
            height: 40px !important;
            min-height: 40px !important;
            padding: 8px 16px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: 1px solid var(--border-strong) !important;
            background-color: #FFFFFF !important;
            color: var(--text-primary) !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.15s ease !important;
        }

        .stButton button:hover {
            background-color: var(--bg-soft) !important;
            border-color: var(--primary) !important;
            color: var(--primary-hover) !important;
        }

        button[kind="primary"], button[data-testid="stBaseButton-primary"] {
            background-color: var(--primary) !important;
            color: #FFFFFF !important;
            border-color: var(--primary) !important;
        }

        button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
            background-color: var(--primary-hover) !important;
            color: #FFFFFF !important;
            border-color: var(--primary-hover) !important;
        }

        /* Rationale: Style native st.form and st.expander containers with uniform card background and border. */
        div[data-testid="stForm"], div[data-testid="stExpander"] {
            background-color: var(--bg-surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            box-shadow: var(--shadow-sm) !important;
        }

        /* Rationale: Style native st.metric cards with uniform card background, border, font sizes, and spacing. */
        div[data-testid="stMetric"] {
            background-color: var(--bg-surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            padding: 14px 16px !important;
            box-shadow: var(--shadow-sm) !important;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 12px !important;
            font-weight: 700 !important;
            color: var(--text-secondary) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
        }

        /* Rationale: Ensure dataframe container has consistent borders and radius matching design system. */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }

        /* Non-fixed Footer Container */
        .static-footer-container {
            margin-top: 40px;
            padding: 20px 0 10px 0;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 12.5px;
            color: var(--text-secondary);
        }
    </style>
    """, unsafe_allow_html=True)


def get_icon_svg(icon_name: str, size: int = 18, color: str = None) -> str:
    """Load 2D SVG icon from assets/icons/{icon_name}.svg and return inline SVG string."""
    svg_path = os.path.join(_ICONS_DIR, f"{icon_name}.svg")
    if not os.path.exists(svg_path):
        return ""
    
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read().replace('\n', ' ').replace('\r', ' ').strip()
    
    if color:
        svg_content = svg_content.replace('#5B5BD6', color).replace('#10B981', color)
    
    svg_content = svg_content.replace('width="24"', f'width="{size}"').replace('height="24"', f'height="{size}"')
    
    return svg_content


def AppFooter(lang: str = "vi"):
    """Vô hiệu hóa Footer theo yêu cầu giao diện."""
    pass


def PageHeader(title: str, subtitle: str):
    """Render Page Header chuẩn hóa."""
    st.markdown(f"""
    <div style="margin-bottom: 20px; margin-top: 0px;">
        <h2 style="margin:0; font-size:22px; font-weight:800; color:var(--text-primary) !important;">{title}</h2>
        {f'<div style="font-size:13.5px; color:var(--text-secondary) !important; margin-top:2px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def InsightCard(icon: str, title: str, text: str):
    """Render Insight Card sử dụng Streamlit Native Container."""
    with st.container(border=True):
        st.markdown(f"<div style='font-weight:700; font-size:14px; color:var(--text-primary); margin-bottom:4px;'>{icon} {title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px; color:var(--text-secondary); line-height:1.5;'>{text}</div>", unsafe_allow_html=True)


def PastelCard(title: str, items: List[Dict[str, Any]], card_type: str = "danger"):
    """Render Status Card tương thích với Light Theme dùng Streamlit Native Container."""
    bg_color = "rgba(239, 68, 68, 0.05)" if card_type == "danger" else "rgba(245, 158, 11, 0.05)" if card_type == "warning" else "rgba(34, 197, 94, 0.05)"
    border_color = "rgba(239, 68, 68, 0.2)" if card_type == "danger" else "rgba(245, 158, 11, 0.2)" if card_type == "warning" else "rgba(34, 197, 94, 0.2)"
    title_color = "#EF4444" if card_type == "danger" else "#F59E0B" if card_type == "warning" else "#22C55E"
    
    with st.container(border=True):
        st.markdown(f"##### {title}")
        if items:
            for item in items:
                st.markdown(f"""
                <div style="background-color:{bg_color}; border:1px solid {border_color}; border-radius:8px; padding:12px 14px; margin-bottom:10px;">
                    <div style="font-weight:700; font-size:13.5px; color:{title_color};">{item.get('title', item.get('name', ''))}</div>
                    <div style="font-size:12.5px; margin-top:4px; color:var(--text-secondary);">{item.get('detail', item.get('reason', item.get('note', '')))}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Không phát hiện dữ liệu phù hợp.")


def EmptyState(title: str, description: str, icon: str = "♟️", cta_label: str = None, cta_key: str = None, on_cta_click = None):
    """Render Empty State bằng Streamlit Native Container."""
    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align:center; padding:24px 12px;">
            <div style="font-size:48px; margin-bottom:12px;">{icon}</div>
            <h3 style="margin:0; font-size:20px; font-weight:800; color:#0F172A;">{title}</h3>
            <p style="font-size:14px; color:#475569; max-width:500px; margin:8px auto 16px auto; line-height:1.5;">
                {description}
            </p>
        </div>
        """, unsafe_allow_html=True)
        if cta_label:
            c1, c2, c3 = st.columns([3, 4, 3])
            with c2:
                if st.button(f"🚀 {cta_label}", type="primary", use_container_width=True, key=cta_key):
                    if on_cta_click:
                        on_cta_click()


def PlaystyleMeter(label_left: str, label_right: str, pct: int, desc: str = ""):
    """Render Playstyle progress meter bar."""
    st.markdown(f"""
    <div style="margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
            <span>{label_left}</span>
            <span style="color:var(--primary);">{pct}% - {label_right}</span>
        </div>
        <div style="height: 8px; background-color: var(--border); border-radius: 4px; overflow: hidden;">
            <div style="height: 100%; width: {pct}%; background-color: var(--primary); border-radius: 4px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def RenderDataTable(df: pd.DataFrame, lang: str):
    """Format và hiển thị Dataframe Repertoire chuẩn Tiếng Việt/English không hiện index."""
    col_map = {
        "name": t("col_move", lang=lang) if lang == "en" else "Khai cuộc",
        "games_count": t("col_games", lang=lang) if lang == "en" else "Số ván",
        "usage_pct": t("col_usage", lang=lang) if lang == "en" else "Tần suất (%)",
        "score_pct": t("col_score", lang=lang) if lang == "en" else "Điểm số (%)",
        "wins": t("metric_wins", lang=lang) if lang == "en" else "Thắng",
        "draws": t("metric_draws", lang=lang) if lang == "en" else "Hòa",
        "losses": t("metric_losses", lang=lang) if lang == "en" else "Thua",
    }
    
    df_clean = df.rename(columns=col_map)
    cols = list(col_map.values())
    valid_cols = [c for c in cols if c in df_clean.columns]
    
    st.dataframe(
        df_clean[valid_cols],
        hide_index=True,
        use_container_width=True
    )

