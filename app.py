import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import chess

from src.pgn_parser import parse_pgn, extract_players, detect_primary_player, filter_games_by_player, OPENING_LOOKUP
from src.statistics import calculate_game_stats
from src.opening_tree import build_opening_tree, get_position_details
from src.board_component import render_interactive_board
from src.move_history_component import render_move_history_component
from src.player_profile import analyze_opening_repertoire, generate_player_insights, generate_deep_opponent_profile
from src.match_prep import generate_match_preparation, generate_actionable_match_preparation
from src.report_generator import generate_markdown_report
from src.online_fetcher import fetch_lichess_games, fetch_chesscom_games
from src.engine.stockfish_engine import StockfishEngine
from src.engine.evaluator import batch_analyze_games, get_comprehensive_move_evaluations, parallel_batch_analyze_games
from src.i18n import t
from src.ui_components import (
    apply_global_styles,
    AppFooter,
    PageHeader,
    InsightCard,
    PastelCard,
    EmptyState,
    RenderDataTable,
    AnalysisProgressTracker,
    COLOR_WIN,
    COLOR_DRAW,
    COLOR_LOSS,
    COLOR_WARNING,
    COLOR_PRIMARY,
    COLOR_BLUE,
    get_icon_svg,
)

# Set Page Config
st.set_page_config(
    page_title="Chess Opponent Analyzer",
    page_icon="assets/icons/app_logo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def _get_cached_stockfish_engine():
    return StockfishEngine()

def get_stockfish_engine():
    eng = _get_cached_stockfish_engine()
    if not eng.is_available():
        st.cache_resource.clear()
        eng = _get_cached_stockfish_engine()
    return eng

# Initialize Session State Variables
if "language" not in st.session_state:
    st.session_state.language = "vi"

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "light"

if "active_nav_page" not in st.session_state:
    st.session_state.active_nav_page = "Dashboard"

if "chess_board" not in st.session_state:
    st.session_state.chess_board = chess.Board()

if "move_history" not in st.session_state:
    st.session_state.move_history = []

if "full_analysis_line" not in st.session_state:
    st.session_state.full_analysis_line = []

if "board_orientation" not in st.session_state:
    st.session_state.board_orientation = "white"

if "user_match_color" not in st.session_state:
    st.session_state.user_match_color = "white"

if "last_selected_player" not in st.session_state:
    st.session_state.last_selected_player = None

if "last_board_timestamp" not in st.session_state:
    st.session_state.last_board_timestamp = 0

if "online_pgn_bytes" not in st.session_state:
    st.session_state.online_pgn_bytes = None

if "online_pgn_name" not in st.session_state:
    st.session_state.online_pgn_name = ""

# Memoization Cache trong Session State
if "analysis_color_filter" not in st.session_state:
    st.session_state.analysis_color_filter = "all"

if "cached_fen_map" not in st.session_state:
    st.session_state.cached_fen_map = {}

if "cached_fen_map_white" not in st.session_state:
    st.session_state.cached_fen_map_white = {}

if "cached_fen_map_black" not in st.session_state:
    st.session_state.cached_fen_map_black = {}

if "cached_stats" not in st.session_state:
    st.session_state.cached_stats = {}

if "cached_repertoire" not in st.session_state:
    st.session_state.cached_repertoire = {}

if "cached_filtered_games" not in st.session_state:
    st.session_state.cached_filtered_games = []

if "cached_move_evaluations" not in st.session_state:
    st.session_state.cached_move_evaluations = None

if "cached_deep_profile" not in st.session_state:
    st.session_state.cached_deep_profile = None

if "cached_profile_lang" not in st.session_state:
    st.session_state.cached_profile_lang = None

# Pawn Structure Explorer Mode State
if "selected_structure" not in st.session_state:
    st.session_state.selected_structure = None

if "structure_games" not in st.session_state:
    st.session_state.structure_games = []

if "selected_structure_game" not in st.session_state:
    st.session_state.selected_structure_game = None

if "structure_explorer_filter" not in st.session_state:
    st.session_state.structure_explorer_filter = "All"

if "skip_board_reset_on_nav" not in st.session_state:
    st.session_state.skip_board_reset_on_nav = False

if "previous_nav_page" not in st.session_state:
    st.session_state.previous_nav_page = st.session_state.active_nav_page

# Áp dụng Global Design System CSS & Theme Mode (Light Mode)
apply_global_styles(theme_mode="light")


# Caching cho hàm Parse PGN để chỉ parse 1 LẦN DUY NHẤT khi upload/tải file
@st.cache_data(show_spinner="⏳ Đang bóc tách dữ liệu PGN...")
def cached_parse_pgn(file_bytes: bytes):
    return parse_pgn(file_bytes)


# State Mutator Functions
def push_move(san_move: str):
    try:
        move_obj = st.session_state.chess_board.parse_san(san_move)
        st.session_state.chess_board.push(move_obj)
        current_ply = len(st.session_state.move_history)
        st.session_state.move_history.append(san_move)

        full_line = st.session_state.full_analysis_line
        if current_ply < len(full_line) and full_line[current_ply] == san_move:
            # Tiếp tục di chuyển trên dòng phân tích sẵn có -> Giữ nguyên full_analysis_line
            pass
        else:
            # Nước đi mới tạo nhánh biến mới -> Cập nhật full_analysis_line
            st.session_state.full_analysis_line = list(st.session_state.move_history)
    except Exception as e:
        st.error(f"Nước đi không hợp lệ '{san_move}': {e}")


def pop_move():
    if len(st.session_state.move_history) > 0:
        st.session_state.chess_board.pop()
        st.session_state.move_history.pop()


def reset_to_first():
    st.session_state.chess_board.reset()
    st.session_state.move_history = []


def step_next():
    history_len = len(st.session_state.move_history)
    full_len = len(st.session_state.full_analysis_line)
    if history_len < full_len:
        next_move = st.session_state.full_analysis_line[history_len]
        push_move(next_move)


def step_last():
    full_len = len(st.session_state.full_analysis_line)
    while len(st.session_state.move_history) < full_len:
        step_next()


def toggle_orientation():
    st.session_state.board_orientation = (
        "black" if st.session_state.board_orientation == "white" else "white"
    )


def jump_to_move_index(target_index: int):
    """Nhảy trực tiếp đến nước đi thứ target_index trong lịch sử đấu."""
    st.session_state.chess_board.reset()
    full_line = st.session_state.full_analysis_line
    st.session_state.move_history = []
    for i in range(min(target_index + 1, len(full_line))):
        m = full_line[i]
        try:
            move_obj = st.session_state.chess_board.parse_san(m)
            st.session_state.chess_board.push(move_obj)
            st.session_state.move_history.append(m)
        except Exception:
            break


def load_single_game_onto_board(game_info: dict):
    """Nạp toàn bộ nước đi của ván đấu lên bàn cờ phân tích và mở trang Analyze Games."""
    moves = game_info.get("moves", [])
    st.session_state.chess_board.reset()
    st.session_state.move_history = []
    for m in moves:
        try:
            move_obj = st.session_state.chess_board.parse_san(m)
            st.session_state.chess_board.push(move_obj)
            st.session_state.move_history.append(m)
        except Exception:
            break
    st.session_state.full_analysis_line = list(st.session_state.move_history)
    st.session_state.skip_board_reset_on_nav = True
    st.session_state.active_nav_page = "Analyze"
    st.rerun()


def find_common_move_prefix(games: list) -> list:
    """Tìm chuỗi nước đi SAN đầu tiên giống nhau (longest common prefix) giữa tất cả các ván đấu."""
    if not games:
        return []
    all_game_moves = [g.get("moves", []) for g in games if g.get("moves")]
    if not all_game_moves:
        return []

    common = []
    min_len = min(len(m) for m in all_game_moves)
    for i in range(min_len):
        move_i = all_game_moves[0][i]
        if all(m[i] == move_i for m in all_game_moves):
            common.append(move_i)
        else:
            break
    return common


def find_representative_line_for_games(games: list) -> list:
    """
    Phân tích thế cờ (position & transposition analysis) trong nhóm ván đấu để tìm
    thế cờ đặc trưng (canonical position) xuất hiện phổ biến nhất và sinh chuỗi
    nước đi đại diện (representative line) dẫn đến thế cờ đó.
    Sử dụng EPD key (quân cờ + lượt đi + nhập thành + bắt tốt qua đường) để khớp transposition chuẩn xác.
    """
    if not games:
        return []
    if len(games) == 1:
        return games[0].get("moves", [])

    fen_info = {}
    start_key = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"

    for g_idx, game in enumerate(games):
        moves = game.get("moves", [])
        if not moves:
            continue
        board = chess.Board()
        root_key = " ".join(board.fen().split()[:4])

        if root_key not in fen_info:
            fen_info[root_key] = {"games": set(), "paths": {}}
        fen_info[root_key]["games"].add(g_idx)
        fen_info[root_key]["paths"][()] = fen_info[root_key]["paths"].get((), 0) + 1

        current_path = []
        for san in moves:
            try:
                move_obj = board.parse_san(san)
                board.push(move_obj)
                current_path.append(san)
                next_key = " ".join(board.fen().split()[:4])

                if next_key not in fen_info:
                    fen_info[next_key] = {"games": set(), "paths": {}}
                fen_info[next_key]["games"].add(g_idx)
                path_tuple = tuple(current_path)
                fen_info[next_key]["paths"][path_tuple] = (
                    fen_info[next_key]["paths"].get(path_tuple, 0) + 1
                )
            except ValueError:
                break

    if not fen_info:
        return []

    non_root_counts = [
        len(info["games"]) for key, info in fen_info.items() if key != start_key
    ]
    if not non_root_counts:
        return []

    max_games_count = max(non_root_counts)
    threshold = max(2, int(max_games_count * 0.75))

    best_key = None
    max_depth = -1

    for key, info in fen_info.items():
        if key == start_key:
            continue
        g_count = len(info["games"])
        if g_count >= threshold:
            for path_tuple in info["paths"].keys():
                depth = len(path_tuple)
                if depth > max_depth:
                    max_depth = depth
                    best_key = key
                elif depth == max_depth and best_key is not None:
                    if g_count > len(fen_info[best_key]["games"]):
                        best_key = key

    if not best_key:
        return find_common_move_prefix(games)

    best_paths = fen_info[best_key]["paths"]
    most_common_path = max(best_paths.items(), key=lambda x: x[1])[0]
    return list(most_common_path)


def get_games_for_opening(opening_name: str, filtered_games: list) -> list:
    """Lọc tất cả các ván đấu trùng khớp với tên khai cuộc."""
    op_clean = opening_name.strip().lower()
    matching = []
    for g in filtered_games:
        g_op = g.get("opening", "").strip().lower()
        if g_op and (op_clean == g_op or op_clean in g_op or g_op in op_clean):
            matching.append(g)

    if not matching:
        for prefix, eco, name in OPENING_LOOKUP:
            if name.lower() in op_clean or op_clean in name.lower():
                prefix_list = list(prefix)
                for g in filtered_games:
                    g_moves = g.get("moves", [])
                    if g_moves[: len(prefix_list)] == prefix_list:
                        matching.append(g)
                break
    return matching


def find_moves_for_opening(opening_name: str, filtered_games: list) -> list:
    """Tìm danh sách nước đi SAN tương ứng với tên khai cuộc."""
    op_clean = opening_name.strip().lower()
    for g in filtered_games:
        g_op = g.get("opening", "").strip().lower()
        if g_op and (g_op == op_clean or op_clean in g_op):
            return g.get("moves", [])

    for prefix, eco, name in OPENING_LOOKUP:
        if name.lower() in op_clean or op_clean in name.lower():
            return list(prefix)
    return []


def load_opening_onto_board(opening_name: str, filtered_games: list, color: str = None):
    """
    Nạp biến khai cuộc lên bàn cờ tương tác và mở trang Analyze Games.
    Sử dụng Position & Transposition Analysis để tìm thế cờ đặc trưng (canonical position)
    và nạp chuỗi nước đi đại diện (representative line) lên bàn cờ theo màu quân tương ứng.
    """
    if color and color.lower() in ["white", "black"]:
        target_color = color.lower()
        st.session_state.analysis_color_filter = target_color
        st.session_state.board_orientation = target_color
        games_subset = [g for g in filtered_games if str(g.get("player_color", "")).lower() == target_color]
        if not games_subset:
            games_subset = filtered_games
    else:
        games_subset = filtered_games

    matching_games = get_games_for_opening(opening_name, games_subset)
    if not matching_games and games_subset is not filtered_games:
        matching_games = get_games_for_opening(opening_name, filtered_games)

    if len(matching_games) == 1:
        load_single_game_onto_board(matching_games[0])
        return

    common_moves = find_representative_line_for_games(matching_games)
    if not common_moves:
        common_moves = find_moves_for_opening(opening_name, matching_games if matching_games else games_subset)

    st.session_state.chess_board.reset()
    st.session_state.move_history = []
    for m in common_moves:
        try:
            move_obj = st.session_state.chess_board.parse_san(m)
            st.session_state.chess_board.push(move_obj)
            st.session_state.move_history.append(m)
        except Exception:
            break
    st.session_state.full_analysis_line = list(st.session_state.move_history)
    st.session_state.skip_board_reset_on_nav = True
    st.session_state.active_nav_page = "Analyze"
    st.rerun()


def load_fen_onto_board(fen_str: str):
    """Load vị trí FEN trực tiếp lên bàn cờ tương tác và mở trang Analyze Games."""
    try:
        st.session_state.chess_board = chess.Board(fen_str)
        st.session_state.move_history = []
        st.session_state.full_analysis_line = []
        st.session_state.skip_board_reset_on_nav = True
        st.session_state.active_nav_page = "Analyze"
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi nạp FEN: {e}")


def load_pawn_structure_onto_board(structure_info: dict):
    """
    Kích hoạt Structure Explorer Mode cho Cấu trúc Tốt được chọn và chuyển sang trang Analyze.
    Đảm bảo danh sách ván đấu luôn được nạp đầy đủ (tính lại nếu cache cũ bị thiếu).
    """
    struct_name = structure_info.get("name", "Pawn Structure")
    games_list = structure_info.get("games", [])
    expected_count = structure_info.get("games_count", 0)

    # Nếu list games rỗng hoặc thiếu games so với games_count, lập tức tính lại từ cached_filtered_games
    if (not games_list or len(games_list) < expected_count) and st.session_state.get("cached_filtered_games"):
        from src.analysis.pawn_structure import analyze_structural_performance
        fresh_struct_res = analyze_structural_performance(
            st.session_state.cached_filtered_games,
            move_evaluations=st.session_state.get("cached_move_evaluations"),
            lang=st.session_state.get("language", "vi")
        )
        target_name_lower = str(struct_name).strip().lower()
        target_key_lower = str(structure_info.get("structure_key", "")).strip().lower()

        for s_item in fresh_struct_res.get("structures", []):
            s_name = s_item.get("name", "").strip().lower()
            s_key = s_item.get("structure_key", "").strip().lower()

            if (s_name and (s_name == target_name_lower or target_name_lower in s_name or s_name in target_name_lower)) or \
               (s_key and s_key == target_key_lower):
                games_list = s_item.get("games", [])
                if st.session_state.get("cached_deep_profile"):
                    st.session_state.cached_deep_profile["structures"] = fresh_struct_res
                break

    st.session_state.selected_structure = struct_name
    st.session_state.structure_games = games_list
    st.session_state.selected_structure_game = None
    st.session_state.structure_explorer_filter = "All"
    st.session_state.skip_board_reset_on_nav = True
    st.session_state.active_nav_page = "Analyze"
    st.rerun()


@st.fragment
def render_analysis_section(fen_map: dict, selected_player: str, lang: str):
    all_player_games = st.session_state.get("cached_filtered_games", [])
    total_cnt = len(all_player_games)
    white_cnt = sum(1 for g in all_player_games if str(g.get("player_color", "")).lower() == "white")
    black_cnt = sum(1 for g in all_player_games if str(g.get("player_color", "")).lower() == "black")

    current_filter = st.session_state.get("analysis_color_filter", "all")

    # Select active fen_map based on color filter
    if current_filter == "white":
        if not st.session_state.get("cached_fen_map_white") and all_player_games:
            _, fm_w = build_opening_tree(all_player_games, color="white")
            st.session_state.cached_fen_map_white = fm_w
        active_fen_map = st.session_state.get("cached_fen_map_white", {})
    elif current_filter == "black":
        if not st.session_state.get("cached_fen_map_black") and all_player_games:
            _, fm_b = build_opening_tree(all_player_games, color="black")
            st.session_state.cached_fen_map_black = fm_b
        active_fen_map = st.session_state.get("cached_fen_map_black", {})
    else:
        active_fen_map = fen_map or st.session_state.get("cached_fen_map", {})

    col_board, col_right = st.columns([5.5, 6.5])

    current_fen = st.session_state.chess_board.fen()
    fen_url = current_fen.replace(" ", "_")
    lichess_url = f"https://lichess.org/analysis/standard/{fen_url}"

    with col_board:
        st.caption(f"{t('opponent', lang=lang)}: **{selected_player}** | {t('view_side', lang=lang)}: **{st.session_state.board_orientation.capitalize()}**")
        
        board_event = render_interactive_board(
            fen=current_fen,
            orientation=st.session_state.board_orientation,
            height=412,
            key="main_interactive_board"
        )

        if board_event and isinstance(board_event, dict):
            ts = board_event.get("timestamp", 0)
            if ts != st.session_state.last_board_timestamp:
                st.session_state.last_board_timestamp = ts
                if "san" in board_event:
                    move_san = board_event["san"]
                    push_move(move_san)
                    st.rerun()
                elif "key_action" in board_event:
                    act = board_event["key_action"]
                    if act == "prev":
                        pop_move()
                    elif act == "next":
                        step_next()
                    elif act == "first":
                        reset_to_first()
                    elif act == "last":
                        step_last()
                    st.rerun()

        # Navigation Controls (Centered under board)
        c_pad1, c_ctrl, c_pad2 = st.columns([0.4, 4.3, 0.4])
        with c_ctrl:
            nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 1, 1, 1])
            with nav1:
                st.button("|<", on_click=reset_to_first, help=t("first_move_btn", lang=lang), use_container_width=True)
            with nav2:
                st.button("<", on_click=pop_move, help=t("prev_move_btn", lang=lang), use_container_width=True)
            with nav3:
                st.button(">", on_click=step_next, help=t("next_move_btn", lang=lang), use_container_width=True)
            with nav4:
                st.button(">|", on_click=step_last, help=t("last_move_btn", lang=lang), use_container_width=True)
            with nav5:
                st.button("", icon=":material/sync:", on_click=toggle_orientation, help=t("flip_board_btn", lang=lang), use_container_width=True)

        st.link_button(
            t("btn_lichess_analysis", lang=lang),
            url=lichess_url,
            help="Mở thế cờ hiện tại trên Lichess Analysis Board",
            use_container_width=True
        )

        with st.expander(t("show_fen", lang=lang), expanded=False):
            st.code(current_fen, language="text")

    # Right Column: Move History (top) + Color Filter + Opening Tree Continuations (bottom)
    with col_right:
        full_line = st.session_state.full_analysis_line
        current_ply = len(st.session_state.move_history) - 1
        pin_icon = get_icon_svg("pin", size=16)
        tree_icon = get_icon_svg("tree", size=18)

        with st.container(border=True):
            st.markdown(f"<div style='font-size:13px; font-weight:700; margin-bottom:4px; color:#0F172A;'>{pin_icon} {t('move_history_title', lang)} ({len(full_line)} plies):</div>", unsafe_allow_html=True)
            
            hist_event = render_move_history_component(
                moves=full_line,
                current_ply=current_ply,
                height=150,
                key="main_move_history_component"
            )

            if hist_event and isinstance(hist_event, dict) and "ply" in hist_event:
                ts = hist_event.get("timestamp", 0)
                if ts != st.session_state.get("last_hist_timestamp", 0):
                    st.session_state.last_hist_timestamp = ts
                    target_ply = int(hist_event["ply"])
                    jump_to_move_index(target_ply)
                    st.rerun()

        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

        # Color Filter Control
        flt_col1, flt_col2, flt_col3 = st.columns(3)
        with flt_col1:
            is_all = current_filter == "all"
            if st.button(
                f"🔄 {t('tree_filter_all', lang=lang, count=total_cnt)}",
                key="btn_flt_all",
                type="primary" if is_all else "secondary",
                use_container_width=True
            ):
                st.session_state.analysis_color_filter = "all"
                st.rerun()

        with flt_col2:
            is_white = current_filter == "white"
            if st.button(
                f"⚪ {t('tree_filter_white', lang=lang, count=white_cnt)}",
                key="btn_flt_white",
                type="primary" if is_white else "secondary",
                use_container_width=True
            ):
                st.session_state.analysis_color_filter = "white"
                st.session_state.board_orientation = "white"
                st.rerun()

        with flt_col3:
            is_black = current_filter == "black"
            if st.button(
                f"⚫ {t('tree_filter_black', lang=lang, count=black_cnt)}",
                key="btn_flt_black",
                type="primary" if is_black else "secondary",
                use_container_width=True
            ):
                st.session_state.analysis_color_filter = "black"
                st.session_state.board_orientation = "black"
                st.rerun()

        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

        pos_details = get_position_details(active_fen_map, current_fen)

        with st.container(border=True):
            if current_filter == "white":
                filter_suffix = f"<span style='font-size:12px; font-weight:600; color:#475569;'> (⚪ {t('white_repertoire', lang=lang)} - {white_cnt} ván)</span>"
            elif current_filter == "black":
                filter_suffix = f"<span style='font-size:12px; font-weight:600; color:#475569;'> (⚫ {t('black_repertoire', lang=lang)} - {black_cnt} ván)</span>"
            else:
                filter_suffix = f"<span style='font-size:12px; font-weight:600; color:#475569;'> ({total_cnt} ván)</span>"

            st.markdown(f"<div style='font-size:15px; font-weight:700; color:#0F172A; margin-bottom:8px;'>{tree_icon} {t('opening_tree_continuations', lang=lang)}{filter_suffix}</div>", unsafe_allow_html=True)

            continuations = pos_details["continuations"]

            if not continuations:
                st.info(t("no_next_moves", lang=lang))
            else:
                h1, h2, h3, h4, h5 = st.columns([1.5, 1.0, 1.2, 3.8, 1.2])
                with h1:
                    st.markdown(f"<div class='continuation-header'>{t('col_move', lang=lang)}</div>", unsafe_allow_html=True)
                with h2:
                    st.markdown(f"<div class='continuation-header'>{t('col_games', lang=lang)}</div>", unsafe_allow_html=True)
                with h3:
                    st.markdown(f"<div class='continuation-header'>{t('col_usage', lang=lang)}</div>", unsafe_allow_html=True)
                with h4:
                    st.markdown(f"<div class='continuation-header'>{t('col_results', lang=lang)}</div>", unsafe_allow_html=True)
                with h5:
                    st.markdown(f"<div class='continuation-header'>{t('col_score', lang=lang)}</div>", unsafe_allow_html=True)

                for cont in continuations:
                    san = cont["san"]
                    g_count = cont["games_count"]
                    usage = cont["usage_pct"]
                    w_pct = cont["win_pct"]
                    d_pct = cont["draw_pct"]
                    l_pct = cont["loss_pct"]
                    score = cont["score_pct"]
                    sg = cont.get("single_game_info")

                    if g_count == 1 and sg:
                        c1, c_game, c_link = st.columns([1.5, 6.2, 1.0])
                        with c1:
                            if st.button(san, icon=":material/play_arrow:", key=f"tree_move_{san}_{len(st.session_state.move_history)}", use_container_width=True, help=f"Đi tiếp nước {san}"):
                                push_move(san)
                                st.rerun()

                        w_name = sg.get("white", "White")
                        w_elo = f"({sg['white_elo']})" if sg.get("white_elo") and sg["white_elo"] > 0 else ""
                        b_name = sg.get("black", "Black")
                        b_elo = f"({sg['black_elo']})" if sg.get("black_elo") and sg["black_elo"] > 0 else ""
                        res = sg.get("result", "*")
                        site_url = sg.get("site", "")
                        has_link = site_url.startswith("http://") or site_url.startswith("https://")
                        game_label = f"{w_name}{w_elo} {res} {b_name}{b_elo}"

                        with c_game:
                            if st.button(game_label, icon=":material/visibility:", key=f"tree_game_{san}_{len(st.session_state.move_history)}", use_container_width=True, help=t("view_single_game_hint", lang=lang)):
                                load_single_game_onto_board(sg)

                        with c_link:
                            if has_link:
                                st.link_button("↗", url=site_url, help="Mở ván đấu nguồn", use_container_width=True)
                            else:
                                st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
                    else:
                        c1, c2, c3, c4, c5 = st.columns([1.5, 1.0, 1.2, 3.8, 1.2])

                        with c1:
                            if st.button(san, icon=":material/play_arrow:", key=f"tree_move_{san}_{len(st.session_state.move_history)}", use_container_width=True):
                                push_move(san)
                                st.rerun()

                        with c2:
                            st.markdown(f"<div style='padding-top:4px; font-weight:600; font-size:13px;'>{g_count}</div>", unsafe_allow_html=True)

                        with c3:
                            st.markdown(f"<div style='padding-top:4px; opacity:0.75; font-size:13px;'>{usage}%</div>", unsafe_allow_html=True)

                        with c4:
                            stacked_bar_html = f"""
                            <div style="padding-top:4px;">
                                <div title="Win: {w_pct}% | Draw: {d_pct}% | Loss: {l_pct}%" 
                                     style="display:flex; height:12px; width:100%; border-radius:3px; overflow:hidden; background-color:rgba(148,163,184,0.2);">
                                    <div style="width:{w_pct}%; background-color:{COLOR_WIN};" title="Win {w_pct}%"></div>
                                    <div style="width:{d_pct}%; background-color:{COLOR_DRAW};" title="Draw {d_pct}%"></div>
                                    <div style="width:{l_pct}%; background-color:{COLOR_LOSS};" title="Loss {l_pct}%"></div>
                                </div>
                                <div style="font-size:11px; opacity:0.8; margin-top:2px;">
                                    <span style="color:#22C55E; font-weight:600;">W {w_pct}%</span> · 
                                    <span style="font-weight:600;">D {d_pct}%</span> · 
                                    <span style="color:#EF4444; font-weight:600;">L {l_pct}%</span>
                                </div>
                            </div>
                            """
                            st.markdown(stacked_bar_html, unsafe_allow_html=True)

                        with c5:
                            st.markdown(f"<div style='padding-top:4px; font-weight:700; color:{COLOR_PRIMARY}; font-size:13px;'>{score}%</div>", unsafe_allow_html=True)


# Active Language
current_lang = st.session_state.language

# ==============================================================================
# UNIFIED UNIFIED STICKY LEFT SIDEBAR
# ==============================================================================
with st.sidebar:
    # Sidebar Header Block (Logo + Title + Slogan tightly coupled)
    st.markdown("""
    <div style="display: flex; align-items: flex-start; gap: 8px; margin-top: 4px; margin-bottom: 8px;">
        <span style="font-size: 24px; line-height: 1; color: #10B981; display: inline-block; margin-top: 2px;">♟</span>
        <div>
            <div style="font-size: 15px; font-weight: 800; line-height: 1.15; color: #1E293B;">Chess Opponent Analyzer</div>
            <div style="font-size: 10px; color: #64748B; margin-top: 3px; line-height: 1.25; font-weight: 400;">Understand your opponent.<br>Prepare with confidence.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Group: ANALYZER
    st.markdown(f"<div class='sidebar-nav-group'>{t('nav_group_analyzer', lang=current_lang)}</div>", unsafe_allow_html=True)
    
    analyzer_pages = [
        ("Dashboard", t("nav_dashboard", lang=current_lang), ":material/dashboard:"),
        ("Analyze", t("nav_analyze_games", lang=current_lang), ":material/analytics:"),
        ("Profile", t("nav_player_profile", lang=current_lang), ":material/person:"),
        ("Prep", t("nav_match_prep", lang=current_lang), ":material/target:"),
    ]

    for p_id, p_name, p_icon in analyzer_pages:
        is_active = st.session_state.active_nav_page == p_id
        if st.button(
            p_name,
            icon=p_icon,
            key=f"side_nav_{p_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.active_nav_page = p_id
            st.rerun()

    # Navigation Group: DATA
    st.markdown(f"<div class='sidebar-nav-group'>{t('nav_group_data', lang=current_lang)}</div>", unsafe_allow_html=True)
    is_active_import = st.session_state.active_nav_page == "Import"
    if st.button(
        t("nav_import_games", lang=current_lang),
        icon=":material/cloud_upload:",
        key="side_nav_Import",
        use_container_width=True,
        type="primary" if is_active_import else "secondary"
    ):
        st.session_state.active_nav_page = "Import"
        st.rerun()

    # Navigation Group: SETTINGS
    st.markdown(f"<div class='sidebar-nav-group'>{t('nav_group_settings', lang=current_lang)}</div>", unsafe_allow_html=True)
    is_active_settings = st.session_state.active_nav_page == "Settings"
    if st.button(
        t("nav_settings", lang=current_lang),
        icon=":material/settings:",
        key="side_nav_Settings",
        use_container_width=True,
        type="primary" if is_active_settings else "secondary"
    ):
        st.session_state.active_nav_page = "Settings"
        st.rerun()

    # Sidebar Bottom Context: CURRENT OPPONENT
    active_bytes = st.session_state.online_pgn_bytes
    active_name = st.session_state.online_pgn_name
    selected_player = None

    if active_bytes is not None:
        try:
            all_games = cached_parse_pgn(active_bytes)
            players_dict = extract_players(all_games)

            if players_dict:
                player_options = list(players_dict.keys())
                primary_player = detect_primary_player(all_games)
                default_index = (
                    player_options.index(primary_player)
                    if primary_player in player_options
                    else 0
                )

                st.markdown("<div style='font-size:11px; font-weight:800; color:#94A3B8; letter-spacing:0.8px; text-transform:uppercase;'>CURRENT OPPONENT</div>", unsafe_allow_html=True)
                
                selected_player = st.selectbox(
                    t("select_player", lang=current_lang),
                    options=player_options,
                    index=default_index,
                    help=t("select_player_help", lang=current_lang),
                    key="sidebar_global_player_select",
                    label_visibility="collapsed"
                )

                if st.session_state.last_selected_player != selected_player or not st.session_state.cached_fen_map:
                    st.session_state.last_selected_player = selected_player
                    reset_to_first()

                    filtered_games = filter_games_by_player(all_games, selected_player)
                    st.session_state.cached_filtered_games = filtered_games

                    stats = calculate_game_stats(filtered_games)
                    st.session_state.cached_stats = stats

                    _, fen_map_all = build_opening_tree(filtered_games, color="all")
                    _, fen_map_white = build_opening_tree(filtered_games, color="white")
                    _, fen_map_black = build_opening_tree(filtered_games, color="black")
                    st.session_state.cached_fen_map = fen_map_all
                    st.session_state.cached_fen_map_white = fen_map_white
                    st.session_state.cached_fen_map_black = fen_map_black

                    repertoire_data = analyze_opening_repertoire(filtered_games)
                    st.session_state.cached_repertoire = repertoire_data

                    # Pre-compute comprehensive evaluations (embedded PGN evals or parallel Stockfish)
                    st.session_state.cached_move_evaluations = None
                    if filtered_games:
                        comp_res = get_comprehensive_move_evaluations(filtered_games, depth=8, max_stockfish_games=20)
                        if comp_res.get("available"):
                            st.session_state.cached_move_evaluations = comp_res.get("move_evaluations", [])

                    # Pre-compute Deep Profile & store in session state for instant load
                    st.session_state.cached_deep_profile = generate_deep_opponent_profile(
                        filtered_games,
                        stats,
                        move_evaluations=st.session_state.cached_move_evaluations,
                        lang=current_lang
                    )
                    st.session_state.cached_profile_lang = current_lang

                st.caption(f"📊 {len(st.session_state.cached_filtered_games)} ván đấu đã phân tích")

                def get_sidebar_report_md():
                    c_prof = st.session_state.cached_deep_profile or {}
                    p_data = generate_actionable_match_preparation(
                        c_prof,
                        user_color=st.session_state.user_match_color,
                        lang=current_lang
                    )
                    return generate_markdown_report(
                        selected_player,
                        st.session_state.cached_stats,
                        st.session_state.cached_repertoire,
                        c_prof.get("rule_insights", []),
                        p_data,
                        user_color=st.session_state.user_match_color
                    )

                st.download_button(
                    label=t("download_report_sidebar", lang=current_lang),
                    data=get_sidebar_report_md(),
                    file_name=f"opponent_report_{selected_player.replace(' ', '_').replace(',', '')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="sidebar_download_report_btn"
                )
        except Exception:
            pass


# RENDER ACTIVE PAGE VIEW
active_page = st.session_state.active_nav_page

# Tự động xóa lịch sử ván đấu & reset bàn cờ khi chuyển giữa các trang khác nhau
if "previous_nav_page" not in st.session_state:
    st.session_state.previous_nav_page = active_page

if active_page != st.session_state.previous_nav_page:
    if not st.session_state.get("skip_board_reset_on_nav", False):
        st.session_state.chess_board.reset()
        st.session_state.move_history = []
        st.session_state.full_analysis_line = []
        st.session_state.last_board_timestamp = 0
        if active_page != "Analyze":
            st.session_state.selected_structure = None
            st.session_state.structure_games = []
            st.session_state.selected_structure_game = None

    st.session_state.skip_board_reset_on_nav = False
    st.session_state.previous_nav_page = active_page

# ==============================================================================
# VIEW 01: DASHBOARD PAGE
# ==============================================================================
if active_page == "Dashboard":
    PageHeader(t("nav_dashboard", lang=current_lang), t("dash_header_subtitle", lang=current_lang))

    if not active_bytes or not selected_player or not st.session_state.cached_stats:
        def on_import_click():
            st.session_state.active_nav_page = "Import"
            st.rerun()

        EmptyState(
            title=t('no_dataset_loaded', lang=current_lang),
            description=t('sidebar_help_upload', lang=current_lang),
            icon="♟️",
            cta_label=t('cta_import_now', lang=current_lang),
            cta_key="dash_empty_cta",
            on_cta_click=on_import_click
        )
    else:
        stats = st.session_state.cached_stats
        repertoire = st.session_state.cached_repertoire

        # 1. HERO BANNER
        with st.container(border=True):
            st.markdown(f"""
            **CHESS OPPONENT ANALYTICS**  
            ### {t('opponent', lang=current_lang)}: {selected_player}
            {t('total_games_analyzed', lang=current_lang, count=stats['total_games'])}
            """) 

        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

        # 2. 5 KPI CARDS
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.metric(t("metric_games", lang=current_lang), stats["total_games"])
        with k2:
            st.metric(t("metric_score", lang=current_lang), f"{stats['score_percentage']}%")
        with k3:
            st.metric(t("metric_wins", lang=current_lang), stats["wins"], delta=f"{stats['win_rate']}%")
        with k4:
            st.metric(t("metric_draws", lang=current_lang), stats["draws"], delta=f"{stats['draw_rate']}%")
        with k5:
            st.metric(t("metric_losses", lang=current_lang), stats["losses"], delta=f"{stats['loss_rate']}%", delta_color="inverse")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 3. KEY INSIGHTS (4 CARDS GRID)
        st.markdown(f"### {t('key_insights_title', lang=current_lang)}")
        
        most_played = repertoire.get("most_played", [])
        best_scoring = repertoire.get("best_scoring", [])
        worst_scoring = repertoire.get("worst_scoring", [])

        fav_op = most_played[0]['name'] if most_played else "N/A"
        fav_desc = f"{most_played[0]['games_count']} ván - Score {most_played[0]['score_pct']}%" if most_played else "Chưa có dữ liệu"

        strong_op = best_scoring[0]['name'] if best_scoring else "N/A"
        strong_desc = f"Score cao nhất {best_scoring[0]['score_pct']}% ({best_scoring[0]['games_count']} ván)" if best_scoring else "Chưa có dữ liệu"

        weak_op = worst_scoring[0]['name'] if worst_scoring else "N/A"
        weak_desc = f"Score thấp nhất {worst_scoring[0]['score_pct']}% ({worst_scoring[0]['games_count']} ván)" if worst_scoring else "Chưa có dữ liệu"

        prep_desc = "Sẵn sàng kế hoạch thi đấu" if current_lang == "vi" else "Ready for match strategy"

        ic1, ic2, ic3, ic4 = st.columns(4)
        with ic1:
            InsightCard("🌿", t("fav_opening_card", lang=current_lang), f"<b>{fav_op}</b><br>{fav_desc}")
        with ic2:
            InsightCard("⚔️", t("strongest_weapon_card", lang=current_lang), f"<b>{strong_op}</b><br>{strong_desc}")
        with ic3:
            InsightCard("📊", t("potential_weakness_card", lang=current_lang), f"<b>{weak_op}</b><br>{weak_desc}")
        with ic4:
            InsightCard("🎯", t("prepare_match_card", lang=current_lang), f"<b>{t('nav_match_prep', lang=current_lang)}</b><br>{prep_desc}")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 4. DASHBOARD CHARTS (Opening Overview & Performance by Color)
        c_left, c_right = st.columns(2)
        with c_left:
            with st.container(border=True):
                st.subheader('Tổng quan Khai cuộc' if current_lang == 'vi' else 'Opening Overview')
                if most_played:
                    op_names = [op['name'][:22] for op in most_played[:5]]
                    op_counts = [op['games_count'] for op in most_played[:5]]
                    fig_op = px.bar(
                        x=op_counts,
                        y=op_names,
                        orientation='h',
                        labels={'x': 'Số ván' if current_lang == 'vi' else 'Games', 'y': 'Khai cuộc' if current_lang == 'vi' else 'Opening'},
                        color_discrete_sequence=['#10B981']
                    )
                    fig_op.update_layout(
                        height=260,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Inter', color='#0F172A'),
                        yaxis=dict(autorange="reversed")
                    )
                    st.plotly_chart(fig_op, use_container_width=True)
                else:
                    st.info("Chưa có thông tin khai cuộc." if current_lang == "vi" else "No opening data available.")

        with c_right:
            with st.container(border=True):
                st.subheader(t('color_perf_title', lang=current_lang))
                fig_perf = go.Figure(data=[
                    go.Bar(name='Wins' if current_lang == 'en' else 'Thắng', x=['White', 'Black'] if current_lang == 'en' else ['Trắng', 'Đen'], y=[stats['white_wins'], stats['black_wins']], marker_color=COLOR_WIN),
                    go.Bar(name='Draws' if current_lang == 'en' else 'Hòa', x=['White', 'Black'] if current_lang == 'en' else ['Trắng', 'Đen'], y=[stats['white_draws'], stats['black_draws']], marker_color=COLOR_DRAW),
                    go.Bar(name='Losses' if current_lang == 'en' else 'Thua', x=['White', 'Black'] if current_lang == 'en' else ['Trắng', 'Đen'], y=[stats['white_losses'], stats['black_losses']], marker_color=COLOR_LOSS)
                ])
                fig_perf.update_layout(
                    barmode='group',
                    height=260,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#0F172A')
                )
                st.plotly_chart(fig_perf, use_container_width=True)

        st.markdown("<div style='margin-bottom:24px;'></div>", unsafe_allow_html=True)

        # 5. QUICK ACTIONS
        st.markdown(f"### {t('quick_actions_header', lang=current_lang)}")
        qa1, qa2, qa3, qa4 = st.columns(4)

        with qa1:
            if st.button(f"{t('nav_analyze_games', lang=current_lang)} →", use_container_width=True, key="qa_analyze"):
                st.session_state.active_nav_page = "Analyze"
                st.rerun()

        with qa2:
            if st.button(f"{t('nav_player_profile', lang=current_lang)} →", use_container_width=True, key="qa_profile"):
                st.session_state.active_nav_page = "Profile"
                st.rerun()

        with qa3:
            if st.button(f"{t('nav_match_prep', lang=current_lang)} →", use_container_width=True, key="qa_prep"):
                st.session_state.active_nav_page = "Prep"
                st.rerun()

        with qa4:
            if st.button(f"{t('nav_import_games', lang=current_lang)} →", use_container_width=True, key="qa_import"):
                st.session_state.active_nav_page = "Import"
                st.rerun()


# ==============================================================================
# VIEW 02: ANALYZE GAMES PAGE
# ==============================================================================
elif active_page == "Analyze":
    PageHeader(t("nav_analyze_games", lang=current_lang), t("workspace_header_subtitle", lang=current_lang))

    if not active_bytes or not selected_player or not st.session_state.cached_fen_map:
        st.info("Vui lòng nạp dữ liệu ván đấu để sử dụng bàn cờ phân tích." if current_lang == "vi" else "Please import game data to use the analysis board.")
        if st.button(f"🚀 {t('cta_import_now', lang=current_lang)}", type="primary", use_container_width=True, key="an_empty_cta"):
            st.session_state.active_nav_page = "Import"
            st.rerun()
    else:
        # MODE B: STRUCTURE EXPLORER HEADER BANNER
        if st.session_state.selected_structure is not None:
            struct_name = st.session_state.selected_structure
            struct_games = st.session_state.structure_games or []

            with st.container(border=True):
                head_col1, head_col2 = st.columns([4.5, 1.5])
                with head_col1:
                    st.markdown(f"### 🧩 STRUCTURE EXPLORER: **{struct_name}**")
                    st.caption(f"Đang xem **{len(struct_games)}** ván đấu thực tế có cấu trúc Tốt này (Move 8–15)." if current_lang == "vi" else f"Exploring **{len(struct_games)}** actual games formed with this structure (Move 8–15).")
                with head_col2:
                    if st.button("⬅️ " + ("Trở về Phân tích Thường" if current_lang == "vi" else "Back to Normal Analysis"), use_container_width=True, key="btn_exit_struct_explorer"):
                        st.session_state.selected_structure = None
                        st.session_state.structure_games = []
                        st.session_state.selected_structure_game = None
                        st.rerun()

            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

        # Render Interactive Chessboard & Move History
        render_analysis_section(st.session_state.cached_fen_map, selected_player, current_lang)

        # MODE B: STRUCTURE GAMES LIST PANEL
        if st.session_state.selected_structure is not None:
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            struct_name = st.session_state.selected_structure
            struct_games = st.session_state.structure_games or []

            with st.container(border=True):
                st.markdown(f"### 📋 {('Danh sách ván đấu có cấu trúc' if current_lang == 'vi' else 'Games with')} **{struct_name}** ({len(struct_games)} {('ván' if current_lang == 'vi' else 'games')})")

                filter_opts = {
                    "All": "Tất cả" if current_lang == "vi" else "All",
                    "Wins": "Ván Thắng" if current_lang == "vi" else "Wins",
                    "Draws": "Ván Hòa" if current_lang == "vi" else "Draws",
                    "Losses": "Ván Thua" if current_lang == "vi" else "Losses",
                }

                selected_filter = st.radio(
                    "Lọc kết quả ván đấu:" if current_lang == "vi" else "Filter game results:",
                    options=list(filter_opts.keys()),
                    format_func=lambda x: filter_opts[x],
                    horizontal=True,
                    key="struct_games_filter_radio"
                )

                filtered_struct_games = []
                for g in struct_games:
                    if selected_filter == "Wins" and not g.get("is_win"):
                        continue
                    if selected_filter == "Draws" and not g.get("is_draw"):
                        continue
                    if selected_filter == "Losses" and not g.get("is_loss"):
                        continue
                    filtered_struct_games.append(g)

                st.markdown("<hr style='margin:8px 0 12px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

                if not filtered_struct_games:
                    st.info("Không có ván đấu nào khớp với bộ lọc." if current_lang == "vi" else "No games match the selected filter.")
                else:
                    gh1, gh2, gh3, gh4 = st.columns([4, 3, 2, 2])
                    gh1.markdown("**Trắng vs Đen**" if current_lang == "vi" else "**White vs Black**")
                    gh2.markdown("**Khai cuộc / Kết quả**" if current_lang == "vi" else "**Opening / Result**")
                    gh3.markdown("**Hình thành**" if current_lang == "vi" else "**Formed**")
                    gh4.markdown("**Thao tác**" if current_lang == "vi" else "**Action**")

                    st.markdown("<hr style='margin:4px 0 8px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

                    for idx, g_info in enumerate(filtered_struct_games):
                        gc1, gc2, gc3, gc4 = st.columns([4, 3, 2, 2])
                        g_idx = g_info.get("game_index", idx)
                        form_move = g_info.get("formation_move", "?")
                        w_name = g_info.get("white", "White")
                        b_name = g_info.get("black", "Black")
                        res = g_info.get("result", "*")
                        op_name = g_info.get("opening", "Unknown Opening")

                        if g_info.get("is_win"):
                            res_badge = f"<span style='color:{COLOR_WIN}; font-weight:700;'>{res} (Thắng)</span>" if current_lang == "vi" else f"<span style='color:{COLOR_WIN}; font-weight:700;'>{res} (Win)</span>"
                        elif g_info.get("is_draw"):
                            res_badge = f"<span style='color:{COLOR_DRAW}; font-weight:700;'>{res} (Hòa)</span>" if current_lang == "vi" else f"<span style='color:{COLOR_DRAW}; font-weight:700;'>{res} (Draw)</span>"
                        elif g_info.get("is_loss"):
                            res_badge = f"<span style='color:{COLOR_LOSS}; font-weight:700;'>{res} (Thua)</span>" if current_lang == "vi" else f"<span style='color:{COLOR_LOSS}; font-weight:700;'>{res} (Loss)</span>"
                        else:
                            res_badge = f"<span>{res}</span>"

                        with gc1:
                            st.markdown(f"**Game #{g_idx + 1}**: ⚪ {w_name} vs ⚫ {b_name}")
                        with gc2:
                            st.markdown(f"{op_name}<br>{res_badge}", unsafe_allow_html=True)
                        with gc3:
                            st.markdown(f"<div style='padding-top:4px;'>Move {form_move}</div>", unsafe_allow_html=True)
                        with gc4:
                            is_current = (st.session_state.selected_structure_game == g_idx)
                            btn_label = "✅ Đang xem" if is_current and current_lang == "vi" else ("✅ Viewing" if is_current else ("👁️ Xem ván" if current_lang == "vi" else "👁️ View Game"))
                            if st.button(
                                btn_label,
                                key=f"btn_view_struct_game_{idx}_{g_idx}",
                                use_container_width=True,
                                disabled=is_current
                            ):
                                all_games = st.session_state.cached_filtered_games
                                if 0 <= g_idx < len(all_games):
                                    target_game = all_games[g_idx]
                                    load_single_game_onto_board(target_game)
                                    st.session_state.selected_structure_game = g_idx
                                    st.rerun()


# ==============================================================================
# VIEW 03: PLAYER PROFILE & DEEP ANALYTICS PAGE
# ==============================================================================
elif active_page in ["Profile", "Performance"]:
    PageHeader(t("nav_player_profile", lang=current_lang), t("profile_header_subtitle", lang=current_lang))

    if not active_bytes or not selected_player or not st.session_state.cached_stats:
        st.info("Vui lòng nạp dữ liệu ván đấu để xem Hồ sơ & Phong độ đối thủ.")
        if st.button("🚀 Nạp Dữ Liệu Ngay", type="primary", use_container_width=True, key="prof_empty_cta"):
            st.session_state.active_nav_page = "Import"
            st.rerun()
    else:
        filtered_games = st.session_state.cached_filtered_games or []
        stats = st.session_state.cached_stats or {}
        engine = get_stockfish_engine()

        # Automatic Stockfish engine execution if evaluations are not yet cached
        if st.session_state.cached_move_evaluations is None and engine.is_available() and filtered_games:
            batch_res = get_comprehensive_move_evaluations(filtered_games, depth=8, max_stockfish_games=20)
            if batch_res.get("available"):
                st.session_state.cached_move_evaluations = batch_res.get("move_evaluations", [])
                st.session_state.cached_deep_profile = None

        # Retrieve or refresh cached deep profile
        is_stale_profile = False
        if st.session_state.cached_deep_profile:
            structs_check = st.session_state.cached_deep_profile.get("structures", {}).get("structures", [])
            if structs_check and "games" not in structs_check[0]:
                is_stale_profile = True

        if st.session_state.cached_deep_profile is None or st.session_state.cached_profile_lang != current_lang or is_stale_profile:
            st.session_state.cached_deep_profile = generate_deep_opponent_profile(
                st.session_state.cached_filtered_games,
                stats,
                move_evaluations=st.session_state.cached_move_evaluations,
                lang=current_lang
            )
            st.session_state.cached_profile_lang = current_lang

        deep_profile = st.session_state.cached_deep_profile

        # 1. Header Card & Engine Status
        head_col1, head_col2 = st.columns([3, 1])
        with head_col1:
            with st.container(border=True):
                st.markdown(f"### ♟ {selected_player}")
                st.caption(f"Đã phân tích **{stats['total_games']}** ván đấu • Score tổng thể: **{stats['score_percentage']}%**" if current_lang == "vi" else f"Analyzed **{stats['total_games']}** games • Overall Score: **{stats['score_percentage']}%**")
        with head_col2:
            with st.container(border=True):
                if engine.is_available():
                    st.success("🟢 Stockfish Active (Depth 8)", icon="🤖")
                    st.caption("Đã tự động phân tích thế cờ ở nền." if current_lang == "vi" else "Positions automatically analyzed in background.")
                else:
                    st.warning("⚠️ Engine Unavailable", icon="🤖")
                    st.caption("Chi tiết thống kê cơ bản vẫn hiển thị đầy đủ." if current_lang == "vi" else "Basic statistics display fully.")

        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

        # 2. Performance 4 KPI Metrics
        pm1, pm2, pm3, pm4 = st.columns(4)
        pm1.metric("Win Rate", f"{stats['win_rate']}%", f"{stats['wins']} Wins")
        pm2.metric("Draw Rate", f"{stats['draw_rate']}%", f"{stats['draws']} Draws")
        pm3.metric("Loss Rate", f"{stats['loss_rate']}%", f"{stats['losses']} Losses", delta_color="inverse")
        pm4.metric("Overall Score", f"{stats['score_percentage']}%", f"{stats['total_games']} Total Games")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 3. Performance Charts
        col_left, col_right = st.columns(2)
        with col_left:
            with st.container(border=True):
                st.markdown("##### Performance theo Màu quân" if current_lang == "vi" else "##### Performance by Color")
                colors_fig = go.Figure(data=[
                    go.Bar(name='Wins', x=['White', 'Black'], y=[stats['white_wins'], stats['black_wins']], marker_color=COLOR_WIN),
                    go.Bar(name='Draws', x=['White', 'Black'], y=[stats['white_draws'], stats['black_draws']], marker_color=COLOR_DRAW),
                    go.Bar(name='Losses', x=['White', 'Black'], y=[stats['white_losses'], stats['black_losses']], marker_color=COLOR_LOSS)
                ])
                colors_fig.update_layout(
                    barmode='group',
                    height=240,
                    margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#0F172A')
                )
                st.plotly_chart(colors_fig, use_container_width=True)

        with col_right:
            with st.container(border=True):
                st.markdown("##### Tỷ lệ Kết quả Ván đấu" if current_lang == "vi" else "##### Game Results Distribution")
                donut_fig = go.Figure(data=[go.Pie(
                    labels=['Wins', 'Draws', 'Losses'],
                    values=[stats['wins'], stats['draws'], stats['losses']],
                    hole=.4,
                    marker_colors=[COLOR_WIN, COLOR_DRAW, COLOR_LOSS],
                    textinfo='label+percent+value'
                )])
                donut_fig.update_layout(
                    height=240,
                    margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#0F172A')
                )
                st.plotly_chart(donut_fig, use_container_width=True)

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"### 🧩 {t('structural_performance_title', lang=current_lang)}")
        struct_list = deep_profile.get("structures", {}).get("structures", [])
        if struct_list:
            with st.container(border=True):
                sh1, sh2, sh3, sh4, sh5, sh6 = st.columns([3.6, 1.0, 1.8, 1.4, 2.4, 1.8])
                sh1.markdown("**Cấu trúc Tốt**" if current_lang == "vi" else "**Pawn Structure**")
                sh2.markdown("**Số ván**" if current_lang == "vi" else "**Games**")
                sh3.markdown("**W / D / L**")
                sh4.markdown("**Raw %**")
                sh5.markdown("**Bayes Adj (Độ tin cậy)**" if current_lang == "vi" else "**Bayes Adj (Confidence)**")
                sh6.markdown("**Thao tác**" if current_lang == "vi" else "**Action**")

                st.markdown("<hr style='margin:4px 0 8px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

                for idx, item in enumerate(struct_list):
                    s1, s2, s3, s4, s5, s6 = st.columns([3.6, 1.0, 1.8, 1.4, 2.4, 1.8])
                    typ_move = item.get("typical_formation_move", 12)
                    raw_s = item.get("score_pct", 0.0)
                    adj_s = item.get("adjusted_score_pct", raw_s)
                    delta = item.get("delta_vs_baseline", 0.0)
                    delta_str = f"+{delta}%" if delta > 0 else f"{delta}%"
                    delta_color = "#22C55E" if delta > 0 else ("#EF4444" if delta < 0 else "#94A3B8")
                    badge = item.get("assessment_badge", "")
                    badge_color = item.get("assessment_color", "#94A3B8")

                    with s1:
                        st.markdown(f"**🧩 {item['name']}**")
                        st.caption(f"Move {typ_move}")
                    with s2:
                        st.markdown(f"<div style='padding-top:8px; color:#475569;'>{item['games_count']} ván</div>" if current_lang == "vi" else f"<div style='padding-top:8px; color:#475569;'>{item['games_count']} g</div>", unsafe_allow_html=True)
                    with s3:
                        st.markdown(f"<div style='padding-top:8px;'><span style='color:#22C55E; font-weight:600;'>{item['wins']}</span>/<span style='color:#94A3B8;'>{item['draws']}</span>/<span style='color:#EF4444; font-weight:600;'>{item['losses']}</span></div>", unsafe_allow_html=True)
                    with s4:
                        st.markdown(f"<div style='padding-top:8px; font-weight:700; color:#1E293B;'>{raw_s}%</div>", unsafe_allow_html=True)
                    with s5:
                        st.markdown(f"<div style='padding-top:4px;'><span style='font-weight:700; color:#4F46E5;'>{adj_s}%</span> <span style='font-size:11px; color:{delta_color}; font-weight:600;'>({delta_str})</span><br><span style='font-size:11.5px; font-weight:600; color:{badge_color};'>{badge}</span></div>", unsafe_allow_html=True)
                    with s6:
                        if st.button(
                            f"🔍 {t('nav_analyze_games', lang=current_lang)}" if current_lang != "vi" else "🔍 Khám phá",
                            key=f"prof_struct_btn_{idx}_{item['name']}",
                            help=f"Bấm để mở Structure Explorer cho {item['name']}" if current_lang == "vi" else f"Click to open Structure Explorer for {item['name']}",
                            use_container_width=True
                        ):
                            load_pawn_structure_onto_board(item)
        else:
            st.info("Chưa phát hiện cấu trúc Tốt đặc trưng." if current_lang == "vi" else "No characteristic pawn structure detected.")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 5. PHASE ACCURACY TABLE (Khai cuộc, Trung cuộc, Tàn cuộc - Dynamic Phase Detection)
        has_engine = deep_profile.get("has_engine_data", False)
        phases_info = deep_profile.get("phases", {}).get("phases", {})
        
        phase_names_map = {
            "opening": ("♟ Khai cuộc", "Opening", "Phát triển quân nhẹ"),
            "middlegame": ("⚔️ Trung cuộc", "Middlegame", "Chiến thuật & Thế trận"),
            "endgame": ("🏆 Tàn cuộc", "Endgame", "Lực lượng tinh giản"),
        }

        with st.container(border=True):
            st.markdown(f"### 📊 {t('phase_accuracy_title', lang=current_lang)}")
            if not has_engine:
                st.info("💡 " + ("Chưa có dữ liệu phân tích từ Stockfish Engine. Hệ thống đang hiển thị thống kê đếm số nước đi phân loại theo từng giai đoạn động:" if current_lang == "vi" else "Stockfish Engine evaluations pending. Showing dynamically classified move counts per phase:"))

            # Table Header
            h1, h2, h3, h4, h5 = st.columns([3.0, 1.8, 1.8, 3.2, 2.2])
            h1.markdown("**Giai đoạn (Phase)**" if current_lang == "vi" else "**Phase**")
            h2.markdown("**Số ván**" if current_lang == "vi" else "**Games**")
            h3.markdown("**Số nước**" if current_lang == "vi" else "**Moves**")
            h4.markdown("**Tỷ lệ Chính xác**" if current_lang == "vi" else "**Accuracy Rate**", help=t("accuracy_tooltip", lang=current_lang))
            h5.markdown("**Đánh giá**" if current_lang == "vi" else "**Assessment**")

            st.markdown("<hr style='margin:4px 0 8px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

            for phase_key in ["opening", "middlegame", "endgame"]:
                p_data = phases_info.get(phase_key, {})
                vi_title, en_title, move_range = phase_names_map[phase_key]
                title_label = vi_title if current_lang == "vi" else en_title

                acc_val = p_data.get("accuracy") or p_data.get("accuracy_pct")
                games_cnt = p_data.get("games_count", 0)
                moves_cnt = p_data.get("analyzed_moves", p_data.get("moves_count", 0))

                if has_engine and acc_val is not None:
                    acc_str = f"{acc_val}%"
                    if acc_val >= 88.0:
                        color = "#22C55E"
                        status = "Xuất sắc" if current_lang == "vi" else "Excellent"
                    elif acc_val >= 75.0:
                        color = "#10B981"
                        status = "Ổn định" if current_lang == "vi" else "Solid"
                    elif acc_val >= 60.0:
                        color = "#F59E0B"
                        status = "Trung bình" if current_lang == "vi" else "Average"
                    else:
                        color = "#EF4444"
                        status = "Cần cải thiện" if current_lang == "vi" else "Needs Work"
                else:
                    acc_str = "N/A"
                    color = "#64748B"
                    status = "Chờ Stockfish" if current_lang == "vi" else "Pending Engine"

                p1, p2, p3, p4, p5 = st.columns([3.0, 1.8, 1.8, 3.2, 2.2])
                with p1:
                    st.markdown(f"**{title_label}**  \n<span style='font-size:11px; color:#64748B;'>{move_range}</span>", unsafe_allow_html=True)
                with p2:
                    st.markdown(f"<div style='padding-top:6px; color:#475569;'>{games_cnt} ván</div>" if current_lang == "vi" else f"<div style='padding-top:6px; color:#475569;'>{games_cnt} g</div>", unsafe_allow_html=True)
                with p3:
                    st.markdown(f"<div style='padding-top:6px; font-weight:600;'>{moves_cnt}</div>", unsafe_allow_html=True)
                with p4:
                    if has_engine and acc_val is not None:
                        st.markdown(f"<div style='font-size:15px; font-weight:800; color:{color};'>{acc_str}</div>", unsafe_allow_html=True)
                        st.progress(float(acc_val) / 100.0)
                    else:
                        st.markdown("<div style='color:#94A3B8; font-weight:600; padding-top:4px;'>N/A</div>", unsafe_allow_html=True)
                with p5:
                    st.markdown(f"<div style='padding-top:6px; font-weight:700; color:{color};'>{status}</div>", unsafe_allow_html=True)

                st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

            # Check coverage of evaluated games and provide On-Demand Deep Analysis button
            total_filtered_games_count = len(filtered_games)
            analyzed_indices = set(e["game_index"] for e in (st.session_state.cached_move_evaluations or []) if "game_index" in e)
            analyzed_games_count = len(analyzed_indices)

            st.markdown("<hr style='margin:12px 0 10px 0; border:0; border-top:1px dashed #E2E8F0;'>", unsafe_allow_html=True)
            
            if total_filtered_games_count > analyzed_games_count and total_filtered_games_count > 0:
                dc1, dc2 = st.columns([7, 3])
                with dc1:
                    st.markdown(
                        f"**🔬 Phân tích Chuyên sâu Toàn bộ**  \n"
                        f"<span style='font-size:12.5px; color:#64748B;'>"
                        f"Đang hiển thị mẫu từ **{analyzed_games_count}/{total_filtered_games_count} ván**. Bấm nút để kích hoạt cụm Stockfish đa luồng phân tích toàn bộ 100% {total_filtered_games_count} ván:"
                        f"</span>" if current_lang == "vi" else
                        f"**🔬 Deep Analysis On-Demand**  \n"
                        f"<span style='font-size:12.5px; color:#64748B;'>"
                        f"Showing sample of **{analyzed_games_count}/{total_filtered_games_count} games**. Click to run multi-threaded Stockfish on all {total_filtered_games_count} games:"
                        f"</span>",
                        unsafe_allow_html=True
                    )
                with dc2:
                    if st.button(
                        f"🚀 Phân tích {total_filtered_games_count} ván" if current_lang == "vi" else f"🚀 Analyze All {total_filtered_games_count} Games",
                        type="primary",
                        use_container_width=True,
                        key="phase_deep_scan_btn"
                    ):
                        progress_bar = st.progress(0, text="Đang khởi chạy Stockfish đa luồng..." if current_lang == "vi" else "Launching parallel Stockfish...")
                        def _on_prog(cur, tot):
                            pct = min(1.0, float(cur) / max(1, tot))
                            progress_bar.progress(pct, text=f"Đang phân tích ván {cur}/{tot} (Bỏ qua {analyzed_games_count} ván có sẵn)..." if current_lang == "vi" else f"Analyzing game {cur}/{tot} (Skipped {analyzed_games_count} cached games)...")

                        deep_eval_res = parallel_batch_analyze_games(
                            filtered_games,
                            depth=8,
                            max_games=total_filtered_games_count,
                            progress_callback=_on_prog,
                            existing_evaluations=st.session_state.cached_move_evaluations
                        )
                        progress_bar.progress(1.0, text="Hoàn tất phân tích chuyên sâu!" if current_lang == "vi" else "Deep analysis complete!")
                        st.session_state.cached_move_evaluations = deep_eval_res.get("move_evaluations", [])
                        st.session_state.cached_deep_profile = generate_deep_opponent_profile(
                            filtered_games,
                            stats,
                            move_evaluations=st.session_state.cached_move_evaluations,
                            lang=current_lang
                        )
                        st.rerun()
            else:
                st.caption(f"✅ Đã phân tích toàn diện 100% dữ liệu ({total_filtered_games_count}/{total_filtered_games_count} ván đấu)" if current_lang == "vi" else f"✅ Comprehensive 100% analysis completed ({total_filtered_games_count}/{total_filtered_games_count} games)")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 6. PLAYING STYLE PROFILE & SIMPLIFICATION
        style_prof = deep_profile.get("style_profile", {})
        scores = style_prof.get("scores", {})
        raw_m = style_prof.get("raw_metrics", {})
        evidence_list = style_prof.get("evidence", [])

        with st.container(border=True):
            st.markdown(f"### 🏆 {t('style_section_title', lang=current_lang)}")
            st.caption(t("style_section_subtitle", lang=current_lang))
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

            # Top Summary Cards: Primary, Secondary, Confidence
            st_c1, st_c2, st_c3 = st.columns([4, 4, 3])
            with st_c1:
                st.markdown(f"**{t('primary_style_label', lang=current_lang)}**")
                p_icon = style_prof.get("primary_icon", "♟️")
                p_name = style_prof.get("primary_style", "N/A")
                p_score = style_prof.get("primary_score", 0.0)
                st.markdown(f"<div style='font-size:18px; font-weight:800; color:#1E293B;'>{p_icon} {p_name} <span style='color:#4F46E5;'>({p_score}%)</span></div>", unsafe_allow_html=True)
                if style_prof.get("archetype"):
                    st.caption(f"{t('style_archetype_label', lang=current_lang)}: *{style_prof['archetype']}*")

            with st_c2:
                st.markdown(f"**{t('secondary_style_label', lang=current_lang)}**")
                s_icon = style_prof.get("secondary_icon", "♟️")
                s_name = style_prof.get("secondary_style", "N/A")
                s_score = style_prof.get("secondary_score", 0.0)
                st.markdown(f"<div style='font-size:17px; font-weight:700; color:#475569;'>{s_icon} {s_name} <span style='color:#64748B;'>({s_score}%)</span></div>", unsafe_allow_html=True)

            with st_c3:
                st.markdown(f"**{t('style_confidence_label', lang=current_lang)}**")
                conf_badge = style_prof.get("confidence_badge", "Medium")
                conf_col = style_prof.get("confidence_color", "#EAB308")
                st.markdown(f"<div style='font-size:15px; font-weight:800; color:{conf_col}; padding-top:4px;'>● {conf_badge}</div>", unsafe_allow_html=True)

            st.markdown("<hr style='margin:14px 0 14px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

            # Style Dimension Bars & Style Evidence
            dim_col1, dim_col2 = st.columns(2)

            with dim_col1:
                st.markdown(f"**{t('style_dimensions_title', lang=current_lang)}**")
                dim_items = [
                    (t("dim_complexity", lang=current_lang), raw_m.get("complexity_index", 50.0)),
                    (t("dim_volatility", lang=current_lang), raw_m.get("volatility_score", 50.0)),
                    (t("dim_queen_retention", lang=current_lang), raw_m.get("queen_retention_25", 50.0)),
                    (t("dim_simplification", lang=current_lang), raw_m.get("simplification_rate", 40.0)),
                    (t("dim_prophylaxis", lang=current_lang), raw_m.get("prophylaxis_rate", 30.0)),
                    (t("dim_resilience", lang=current_lang), raw_m.get("resilience_rate", 50.0)),
                ]
                for d_label, d_val in dim_items:
                    d_c1, d_c2 = st.columns([6, 2])
                    d_c1.markdown(f"<span style='font-size:12.5px; font-weight:600;'>{d_label}</span>", unsafe_allow_html=True)
                    d_c2.markdown(f"<span style='font-size:12.5px; font-weight:800; color:#4F46E5;'>{d_val}</span>", unsafe_allow_html=True)
                    st.progress(float(d_val) / 100.0)

            with dim_col2:
                st.markdown(f"**{t('style_evidence_title', lang=current_lang)}**")
                if evidence_list:
                    for ev_item in evidence_list:
                        st.markdown(f"• <span style='font-size:13px; color:#334155; line-height:1.5;'>{ev_item}</span>", unsafe_allow_html=True)
                else:
                    st.caption("Chưa có đủ dữ liệu để trích xuất bằng chứng." if current_lang == "vi" else "Insufficient data to extract evidence.")

                st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
                
                # Simplification Quick Insight
                simp = deep_profile.get("simplification", {})
                if simp.get("recommendation"):
                    st.info(f"👑 **Simplification**: {simp['recommendation']}")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 7. CRITICAL POSITIONS FOR TRAINING
        st.markdown(f"### 🎓 {t('critical_positions_title', lang=current_lang)}")
        crit_pos = deep_profile.get("critical_positions", [])
        if crit_pos:
            cp_cols = st.columns(min(len(crit_pos), 3))
            for idx, pos in enumerate(crit_pos[:3]):
                with cp_cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"**Critical Move #{pos['move_number']}: {pos['san']}**")
                        st.caption(f"Eval: {pos['eval_before']} → {pos['eval_after']} (CPL {pos['cpl']})")
                        st.code(pos['fen_before'], language=None)
                        if st.button("🎯 Nạp thế cờ lên Bàn cờ Phân tích" if current_lang == "vi" else "🎯 Load Position onto Board", key=f"prof_study_pos_{idx}", use_container_width=True):
                            load_fen_onto_board(pos['fen_before'])
        else:
            if not has_engine:
                st.info(t("engine_pending_notice", lang=current_lang))
            else:
                st.info("Chưa phát hiện thế cờ sụt giảm điểm số lớn từ dữ liệu hiện tại." if current_lang == "vi" else "No critical evaluation drops detected in analyzed games.")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 8. Repertoire Tables
        st.markdown("### 📚 Opening Repertoire Overview")
        c_white, c_black = st.columns(2)
        with c_white:
            with st.container(border=True):
                st.markdown("##### Repertoire cầm Trắng" if current_lang == "vi" else "##### White Repertoire")
                w_rep = deep_profile["repertoire"].get("white_repertoire", [])
                if w_rep:
                    wh1, wh2, wh3, wh4, wh5 = st.columns([4.8, 1.0, 1.8, 1.4, 2.6])
                    wh1.markdown("**Khai cuộc**" if current_lang == "vi" else "**Opening**")
                    wh2.markdown("**Ván**" if current_lang == "vi" else "**G**")
                    wh3.markdown("**W/D/L**")
                    wh4.markdown("**Raw %**")
                    wh5.markdown("**Bayes Adj (Độ tin cậy)**" if current_lang == "vi" else "**Bayes Adj (Confidence)**")

                    st.markdown("<hr style='margin:4px 0 8px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

                    for idx, item in enumerate(w_rep):
                        w1, w2, w3, w4, w5 = st.columns([4.8, 1.0, 1.8, 1.4, 2.6])
                        raw_s = item.get("score_pct", 0.0)
                        adj_s = item.get("adjusted_score_pct", raw_s)
                        delta = item.get("delta_vs_baseline", 0.0)
                        delta_str = f"+{delta}%" if delta > 0 else f"{delta}%"
                        delta_color = "#22C55E" if delta > 0 else ("#EF4444" if delta < 0 else "#94A3B8")
                        badge = item.get("assessment_badge", "")
                        badge_color = item.get("assessment_color", "#94A3B8")

                        with w1:
                            if st.button(
                                f"♟ {item['name']}",
                                key=f"prof_w_op_btn_{idx}_{item['name']}",
                                help=f"Bấm để nạp {item['name']} lên Bàn cờ Phân tích (Cầm Trắng)" if current_lang == "vi" else f"Click to load {item['name']} onto Analysis Board (as White)",
                                use_container_width=True
                            ):
                                load_opening_onto_board(item['name'], st.session_state.cached_filtered_games, color="white")
                        with w2:
                            st.markdown(f"<div style='padding-top:6px; color:#475569;'>{item['games_count']}</div>", unsafe_allow_html=True)
                        with w3:
                            st.markdown(f"<div style='padding-top:6px;'><span style='color:#22C55E; font-weight:600;'>{item['wins']}</span>/<span style='color:#94A3B8;'>{item['draws']}</span>/<span style='color:#EF4444; font-weight:600;'>{item['losses']}</span></div>", unsafe_allow_html=True)
                        with w4:
                            st.markdown(f"<div style='padding-top:6px; font-weight:700; color:#1E293B;'>{raw_s}%</div>", unsafe_allow_html=True)
                        with w5:
                            st.markdown(f"<div style='padding-top:4px;'><span style='font-weight:700; color:#4F46E5;'>{adj_s}%</span> <span style='font-size:10.5px; color:{delta_color}; font-weight:600;'>({delta_str})</span><br><span style='font-size:10.5px; font-weight:600; color:{badge_color};'>{badge}</span></div>", unsafe_allow_html=True)
                else:
                    st.info("Không có dữ liệu khi cầm Trắng." if current_lang == "vi" else "No White repertoire data.")

        with c_black:
            with st.container(border=True):
                st.markdown("##### Repertoire cầm Đen" if current_lang == "vi" else "##### Black Repertoire")
                b_rep = deep_profile["repertoire"].get("black_repertoire", [])
                if b_rep:
                    bh1, bh2, bh3, bh4, bh5 = st.columns([4.8, 1.0, 1.8, 1.4, 2.6])
                    bh1.markdown("**Khai cuộc**" if current_lang == "vi" else "**Opening**")
                    bh2.markdown("**Ván**" if current_lang == "vi" else "**G**")
                    bh3.markdown("**W/D/L**")
                    bh4.markdown("**Raw %**")
                    bh5.markdown("**Bayes Adj (Độ tin cậy)**" if current_lang == "vi" else "**Bayes Adj (Confidence)**")

                    st.markdown("<hr style='margin:4px 0 8px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

                    for idx, item in enumerate(b_rep):
                        b1, b2, b3, b4, b5 = st.columns([4.8, 1.0, 1.8, 1.4, 2.6])
                        raw_s = item.get("score_pct", 0.0)
                        adj_s = item.get("adjusted_score_pct", raw_s)
                        delta = item.get("delta_vs_baseline", 0.0)
                        delta_str = f"+{delta}%" if delta > 0 else f"{delta}%"
                        delta_color = "#22C55E" if delta > 0 else ("#EF4444" if delta < 0 else "#94A3B8")
                        badge = item.get("assessment_badge", "")
                        badge_color = item.get("assessment_color", "#94A3B8")

                        with b1:
                            if st.button(
                                f"♟ {item['name']}",
                                key=f"prof_b_op_btn_{idx}_{item['name']}",
                                help=f"Bấm để nạp {item['name']} lên Bàn cờ Phân tích (Cầm Đen)" if current_lang == "vi" else f"Click to load {item['name']} onto Analysis Board (as Black)",
                                use_container_width=True
                            ):
                                load_opening_onto_board(item['name'], st.session_state.cached_filtered_games, color="black")
                        with b2:
                            st.markdown(f"<div style='padding-top:6px; color:#475569;'>{item['games_count']}</div>", unsafe_allow_html=True)
                        with b3:
                            st.markdown(f"<div style='padding-top:6px;'><span style='color:#22C55E; font-weight:600;'>{item['wins']}</span>/<span style='color:#94A3B8;'>{item['draws']}</span>/<span style='color:#EF4444; font-weight:600;'>{item['losses']}</span></div>", unsafe_allow_html=True)
                        with b4:
                            st.markdown(f"<div style='padding-top:6px; font-weight:700; color:#1E293B;'>{raw_s}%</div>", unsafe_allow_html=True)
                        with b5:
                            st.markdown(f"<div style='padding-top:4px;'><span style='font-weight:700; color:#4F46E5;'>{adj_s}%</span> <span style='font-size:10.5px; color:{delta_color}; font-weight:600;'>({delta_str})</span><br><span style='font-size:10.5px; font-weight:600; color:{badge_color};'>{badge}</span></div>", unsafe_allow_html=True)
                else:
                    st.info("Không có dữ liệu khi cầm Đen." if current_lang == "vi" else "No Black repertoire data.")


# ==============================================================================
# VIEW 06: MATCH PREPARATION PAGE (DECISION SUPPORT)
# ==============================================================================
elif active_page == "Prep":
    PageHeader(t("nav_match_prep", lang=current_lang), t("prep_header_subtitle", lang=current_lang))

    if not active_bytes or not selected_player or not st.session_state.cached_stats:
        st.info("Vui lòng nạp dữ liệu ván đấu để xem Kế hoạch tác chiến." if current_lang == "vi" else "Please import game data to view match preparation.")
        if st.button(f"🚀 {t('cta_import_now', lang=current_lang)}", type="primary", use_container_width=True, key="prep_empty_cta"):
            st.session_state.active_nav_page = "Import"
            st.rerun()
    else:
        stats = st.session_state.cached_stats
        engine = get_stockfish_engine()

        # Retrieve or compute cached deep profile
        if st.session_state.cached_deep_profile is None or st.session_state.cached_profile_lang != current_lang:
            st.session_state.cached_deep_profile = generate_deep_opponent_profile(
                st.session_state.cached_filtered_games,
                stats,
                move_evaluations=st.session_state.cached_move_evaluations,
                lang=current_lang
            )
            st.session_state.cached_profile_lang = current_lang

        deep_profile = st.session_state.cached_deep_profile

        # Control Row
        col_color, col_down = st.columns([3, 2])
        
        with col_color:
            match_color = st.radio(
                t("your_color_in_match", lang=current_lang),
                options=["white", "black"],
                index=0 if st.session_state.user_match_color == "white" else 1,
                format_func=lambda x: f"⚪ {t('play_white_opt', lang=current_lang)}" if x == "white" else f"🖤 {t('play_black_opt', lang=current_lang)}",
                horizontal=True,
                key="user_match_color_radio"
            )
            st.session_state.user_match_color = match_color

        actionable_prep = generate_actionable_match_preparation(
            deep_profile,
            user_color=match_color,
            lang=current_lang
        )

        with col_down:
            report_md_prep = generate_markdown_report(
                selected_player,
                st.session_state.cached_stats,
                st.session_state.cached_repertoire,
                deep_profile.get("rule_insights", []),
                actionable_prep,
                user_color=match_color
            )
            st.download_button(
                label=t("download_full_report", lang=current_lang),
                data=report_md_prep,
                file_name=f"match_prep_{selected_player.replace(' ', '_').replace(',', '')}.md",
                mime="text/markdown",
                use_container_width=True,
                key="tab_prep_download_report_btn"
            )

        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

        # 1. STRONGEST vs WEAKEST OPENING (Concise Decision Cards)
        st.markdown("### 📚 Opening Strategy Focus")
        op_col1, op_col2 = st.columns(2)

        strong_op = actionable_prep.get("strongest_opening")
        weak_op = actionable_prep.get("weakest_opening")

        with op_col1:
            with st.container(border=True):
                st.markdown(f"##### 🛡️ {t('strongest_opening_title', lang=current_lang)}")
                if strong_op:
                    st.markdown(f"**{strong_op['name']}**")
                    st.caption(f"{strong_op['games_count']} ván • **{strong_op['score_pct']}%** score" if current_lang == "vi" else f"{strong_op['games_count']} games • **{strong_op['score_pct']}%** score")
                    st.warning("Khuyên dùng: Tránh né biến chính mạnh nhất của đối thủ trừ khi đã chuẩn bị kỹ." if current_lang == "vi" else "Recommendation: Avoid entering opponent's strongest line unless specifically prepared.")
                else:
                    st.caption("Chưa phát hiện biến mở đầu vượt trội." if current_lang == "vi" else "No strong opening baseline detected.")

        with op_col2:
            with st.container(border=True):
                st.markdown(f"##### ⚔️ {t('weakest_opening_title', lang=current_lang)}")
                if weak_op:
                    st.markdown(f"**{weak_op['name']}**")
                    st.caption(f"{weak_op['games_count']} ván • **{weak_op['score_pct']}%** score" if current_lang == "vi" else f"{weak_op['games_count']} games • **{weak_op['score_pct']}%** score")
                    st.success("Khuyên dùng: Chủ động hướng trận đấu vào thế cờ đối thủ đạt hiệu suất kém." if current_lang == "vi" else "Recommendation: Consider lines that can lead toward this structure.")
                else:
                    st.caption("Chưa phát hiện điểm yếu mở đầu rõ rệt." if current_lang == "vi" else "No weak opening baseline detected.")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 2. DECISION SUPPORT BLOCKS (Target Structure, Vulnerability Phase, Game Dynamics)
        b1, b2, b3 = st.columns(3)

        with b1:
            with st.container(border=True):
                st.markdown(f"##### {t('target_structure_title', lang=current_lang)}")
                target_st = actionable_prep.get("target_structure")
                if target_st:
                    st.markdown(f"### {target_st['name']}")
                    st.caption(f"Score: **{target_st['score_pct']}%** | {target_st['games_count']} ván" if current_lang == "vi" else f"Score: **{target_st['score_pct']}%** | {target_st['games_count']} Games")
                    st.info(f"Đối thủ thi đấu kém ở cấu trúc {target_st['name']}." if current_lang == "vi" else f"Opponent performs poorly in positions featuring an {target_st['name']}.")
                    with st.expander("🔍 View Evidence"):
                        st.write(f"Confidence: {target_st['confidence']['label']}")
                        st.write(f"Wins: {target_st['wins']} | Draws: {target_st['draws']} | Losses: {target_st['losses']}")
                else:
                    st.caption("Chưa phát hiện điểm yếu cấu trúc Tốt cụ thể." if current_lang == "vi" else "No specific structural weakness identified.")

        with b2:
            with st.container(border=True):
                st.markdown(f"##### {t('vulnerability_phase_title', lang=current_lang)}")
                weak_phase = actionable_prep.get("vulnerability_phase")
                if weak_phase:
                    st.markdown(f"### {weak_phase.get('phase', '').upper()}")
                    st.caption(f"Average ACPL: **{weak_phase.get('avg_acpl', 0.0)}**")
                    st.warning("Độ chính xác đối thủ giảm ở giai đoạn này." if current_lang == "vi" else "Opponent's accuracy decreases in this phase. Simplify or guide game here.")
                else:
                    st.caption("Phong độ các giai đoạn tương đối cân bằng." if current_lang == "vi" else "Phase performance is balanced.")

        with b3:
            with st.container(border=True):
                st.markdown(f"##### {t('game_dynamics_title', lang=current_lang)}")
                st.markdown(f"Throw Rate: **{actionable_prep.get('throw_rate', 0.0)}%**")
                st.markdown(f"Resilience: **{actionable_prep.get('resilience_rate', 0.0)}%**")
                st.caption("Duy trì áp lực thực chiến dù đang dẫn trước hay bị dẫn điểm." if current_lang == "vi" else "Maintain practical pressure when ahead or behind.")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 3. YOUR FINAL GAME PLAN (PLAY, TARGET, AVOID)
        st.markdown(f"### 📋 {t('game_plan_title', lang=current_lang)}")
        g1, g2, g3 = st.columns(3)

        with g1:
            with st.container(border=True):
                st.markdown(f"#### 🟢 {t('plan_play', lang=current_lang)}")
                for item in actionable_prep.get("play_plan", []):
                    st.markdown(f"• {item}")

        with g2:
            with st.container(border=True):
                st.markdown(f"#### 🟡 {t('plan_target', lang=current_lang)}")
                for item in actionable_prep.get("target_plan", []):
                    st.markdown(f"• {item}")

        with g3:
            with st.container(border=True):
                st.markdown(f"#### 🔴 {t('plan_avoid', lang=current_lang)}")
                for item in actionable_prep.get("avoid_plan", []):
                    st.markdown(f"• {item}")


# ==============================================================================
# VIEW 07: IMPORT GAMES PAGE
# ==============================================================================
elif active_page == "Import":
    PageHeader(t("nav_import_games", lang=current_lang), t("import_header_subtitle", lang=current_lang))

    col_up, col_on = st.columns(2)

    with col_up:
        with st.container(border=True):
            st.markdown("#### 📁 Upload File PGN")
            file_up = st.file_uploader(
                "Kéo thả file PGN vào đây",
                type=["pgn"],
                key="import_page_pgn_file_uploader",
                label_visibility="visible"
            )
            if file_up is not None:
                new_bytes = file_up.getvalue()
                if st.session_state.online_pgn_bytes != new_bytes:
                    progress_placeholder = st.empty()
                    steps_def = [
                        {"id": "parse", "title": f"Bóc tách dữ liệu từ file {file_up.name}" if current_lang == "vi" else f"Parse data from {file_up.name}"},
                        {"id": "tree", "title": "Xây dựng Cây Khai cuộc Trắng / Đen" if current_lang == "vi" else "Build Opening Trees (White / Black / All)"},
                        {"id": "engine", "title": "Phân tích chuyên sâu (Đánh giá có sẵn / Đa luồng)" if current_lang == "vi" else "Deep Analysis (Embedded Evals / Parallel Engine)"},
                        {"id": "ready", "title": "Nạp bàn cờ phân tích và hoàn tất" if current_lang == "vi" else "Prepare Analysis Board & Finalize"},
                    ]
                    tracker = AnalysisProgressTracker(
                        progress_placeholder,
                        steps_def,
                        title=f"Tiến trình nạp file PGN: {file_up.name}" if current_lang == "vi" else f"PGN File Processing: {file_up.name}",
                        lang=current_lang
                    )

                    # Step 1: Parse
                    tracker.set_step_running("parse", "Đang bóc tách PGN..." if current_lang == "vi" else "Parsing PGN...")
                    all_games = cached_parse_pgn(new_bytes)
                    primary_player = detect_primary_player(all_games)
                    target_player = primary_player if primary_player else "Unknown Player"
                    tracker.set_step_done("parse", f"Đã nhận diện {len(all_games)} ván đấu (Kỳ thủ: {target_player})" if current_lang == "vi" else f"Found {len(all_games)} games (Player: {target_player})")

                    # Step 2: Tree
                    tracker.set_step_running("tree", "Đang tính toán các biến và thống kê..." if current_lang == "vi" else "Computing variations & statistics...")
                    filtered_games = filter_games_by_player(all_games, target_player)
                    stats = calculate_game_stats(filtered_games)
                    _, fen_map_all = build_opening_tree(filtered_games, color="all")
                    _, fen_map_white = build_opening_tree(filtered_games, color="white")
                    _, fen_map_black = build_opening_tree(filtered_games, color="black")
                    repertoire_data = analyze_opening_repertoire(filtered_games)
                    tracker.set_step_done("tree", f"Đã tạo 3 cây khai cuộc (Tất cả: {len(fen_map_all)}, Trắng: {len(fen_map_white)}, Đen: {len(fen_map_black)} thế cờ)" if current_lang == "vi" else f"Built 3 opening trees (All, White, Black)")

                    # Step 3: Engine
                    tracker.set_step_running("engine", "Đang đánh giá chất lượng nước đi..." if current_lang == "vi" else "Evaluating positions & pawn structures...")
                    comp_res = get_comprehensive_move_evaluations(filtered_games, depth=8, max_stockfish_games=20)
                    move_evals = comp_res.get("move_evaluations", []) if comp_res.get("available") else None
                    if comp_res.get("source") == "embedded_pgn":
                        eval_msg = f"Đã trích xuất đánh giá chất lượng cao từ {comp_res.get('analyzed_games', 0)} ván đấu (0s)" if current_lang == "vi" else f"Extracted embedded evaluations from {comp_res.get('analyzed_games', 0)} games (0s)"
                    else:
                        eval_msg = f"Đã phân tích đa luồng ({comp_res.get('analyzed_games', 0)} ván đấu)" if current_lang == "vi" else f"Parallel analyzed {comp_res.get('analyzed_games', 0)} games"

                    deep_profile = generate_deep_opponent_profile(
                        filtered_games,
                        stats,
                        move_evaluations=move_evals,
                        lang=current_lang
                    )
                    tracker.set_step_done("engine", eval_msg)

                    # Step 4: Ready
                    tracker.set_step_running("ready", "Đang nạp bàn cờ..." if current_lang == "vi" else "Loading board...")
                    st.session_state.online_pgn_bytes = new_bytes
                    st.session_state.online_pgn_name = file_up.name
                    st.session_state.last_selected_player = target_player
                    st.session_state.cached_filtered_games = filtered_games
                    st.session_state.cached_stats = stats
                    st.session_state.cached_fen_map = fen_map_all
                    st.session_state.cached_fen_map_white = fen_map_white
                    st.session_state.cached_fen_map_black = fen_map_black
                    st.session_state.cached_repertoire = repertoire_data
                    st.session_state.cached_move_evaluations = move_evals
                    st.session_state.cached_deep_profile = deep_profile
                    st.session_state.cached_profile_lang = current_lang
                    tracker.set_step_done("ready", "Sẵn sàng phân tích!" if current_lang == "vi" else "Ready to analyze!")

                    st.session_state.active_nav_page = "Analyze"
                    st.rerun()

    with col_on:
        with st.container(border=True):
            st.markdown("#### 🌐 Fetch từ Lichess / Chess.com")
            platform = st.selectbox(t("platform_select", lang=current_lang), options=["Lichess", "Chess.com"], key="import_page_platform_select")
            online_user = st.text_input(t("username_label", lang=current_lang), placeholder=t("username_placeholder", lang=current_lang), key="import_page_user_input")
            max_games_input = st.number_input(
                t("max_games_label", lang=current_lang),
                min_value=1,
                max_value=300,
                value=None,
                step=10,
                placeholder=t("max_games_placeholder", lang=current_lang),
                key="import_page_max_games"
            )
            max_games = int(max_games_input) if max_games_input is not None else 50
            selected_game_types = st.multiselect(
                t("game_type_label", lang=current_lang),
                options=["Bullet", "Blitz", "Rapid", "Classical", "Daily / Correspondence"],
                default=[],
                help=t("game_type_help", lang=current_lang),
                key="import_page_game_types"
            )

            if st.button(t("btn_fetch_games", lang=current_lang), type="primary", use_container_width=True, key="import_page_fetch_online_btn"):
                if online_user.strip():
                    progress_placeholder = st.empty()
                    steps_def = [
                        {"id": "fetch", "title": f"Tải {max_games} ván đấu của {online_user} từ {platform}" if current_lang == "vi" else f"Fetch {max_games} games for {online_user} from {platform}"},
                        {"id": "parse", "title": "Bóc tách dữ liệu PGN và phát hiện kỳ thủ" if current_lang == "vi" else "Parse PGN data & detect opponent"},
                        {"id": "tree", "title": "Xây dựng Cây Khai cuộc Trắng / Đen" if current_lang == "vi" else "Build Opening Trees (White / Black / All)"},
                        {"id": "engine", "title": "Phân tích chuyên sâu (Đánh giá có sẵn / Đa luồng)" if current_lang == "vi" else "Deep Analysis (Embedded Evals / Parallel Engine)"},
                        {"id": "ready", "title": "Nạp bàn cờ phân tích và hoàn tất" if current_lang == "vi" else "Prepare Analysis Board & Finalize"},
                    ]
                    tracker = AnalysisProgressTracker(
                        progress_placeholder,
                        steps_def,
                        title=f"Tiến trình nạp và phân tích ván đấu ({platform})" if current_lang == "vi" else f"Data Loading & Analysis Pipeline ({platform})",
                        lang=current_lang
                    )

                    # Step 1: Fetch
                    tracker.set_step_running("fetch", "Đang kết nối máy chủ..." if current_lang == "vi" else "Connecting to server...")
                    if platform == "Lichess":
                        pgn_bytes, err = fetch_lichess_games(online_user, max_games, perf_types=selected_game_types)
                    else:
                        pgn_bytes, err = fetch_chesscom_games(online_user, max_games, perf_types=selected_game_types)

                    if err:
                        tracker.set_step_error("fetch", f"Lỗi tải ván đấu: {err}" if current_lang == "vi" else f"Fetch error: {err}")
                        st.error(err)
                    elif pgn_bytes:
                        tracker.set_step_done("fetch", f"Đã tải thành công ván đấu từ {platform}" if current_lang == "vi" else f"Successfully fetched games from {platform}")

                        # Step 2: Parse
                        tracker.set_step_running("parse", "Đang bóc tách PGN..." if current_lang == "vi" else "Parsing PGN...")
                        all_games = cached_parse_pgn(pgn_bytes)
                        primary_player = detect_primary_player(all_games)
                        target_player = primary_player if primary_player else online_user
                        tracker.set_step_done("parse", f"Đã nhận diện {len(all_games)} ván đấu (Kỳ thủ: {target_player})" if current_lang == "vi" else f"Found {len(all_games)} games (Player: {target_player})")

                        # Step 3: Tree
                        tracker.set_step_running("tree", "Đang tính toán các biến và thống kê..." if current_lang == "vi" else "Computing variations & statistics...")
                        filtered_games = filter_games_by_player(all_games, target_player)
                        stats = calculate_game_stats(filtered_games)
                        _, fen_map_all = build_opening_tree(filtered_games, color="all")
                        _, fen_map_white = build_opening_tree(filtered_games, color="white")
                        _, fen_map_black = build_opening_tree(filtered_games, color="black")
                        repertoire_data = analyze_opening_repertoire(filtered_games)
                        tracker.set_step_done("tree", f"Đã tạo 3 cây khai cuộc (Tất cả: {len(fen_map_all)}, Trắng: {len(fen_map_white)}, Đen: {len(fen_map_black)} thế cờ)" if current_lang == "vi" else f"Built 3 opening trees (All, White, Black)")

                        # Step 4: Engine & Deep Profile
                        tracker.set_step_running("engine", "Đang đánh giá chất lượng nước đi..." if current_lang == "vi" else "Evaluating positions & pawn structures...")
                        comp_res = get_comprehensive_move_evaluations(filtered_games, depth=8, max_stockfish_games=20)
                        move_evals = comp_res.get("move_evaluations", []) if comp_res.get("available") else None
                        if comp_res.get("source") == "embedded_pgn":
                            eval_msg = f"Đã trích xuất đánh giá chất lượng cao từ {comp_res.get('analyzed_games', 0)} ván đấu (0s)" if current_lang == "vi" else f"Extracted embedded evaluations from {comp_res.get('analyzed_games', 0)} games (0s)"
                        else:
                            eval_msg = f"Đã phân tích đa luồng ({comp_res.get('analyzed_games', 0)} ván đấu)" if current_lang == "vi" else f"Parallel analyzed {comp_res.get('analyzed_games', 0)} games"

                        deep_profile = generate_deep_opponent_profile(
                            filtered_games,
                            stats,
                            move_evaluations=move_evals,
                            lang=current_lang
                        )
                        tracker.set_step_done("engine", eval_msg)

                        # Step 5: Ready
                        tracker.set_step_running("ready", "Đang lưu bộ nhớ và chuyển trang..." if current_lang == "vi" else "Saving state and loading board...")
                        st.session_state.online_pgn_bytes = pgn_bytes
                        st.session_state.online_pgn_name = f"{platform}_{online_user}.pgn"
                        st.session_state.last_selected_player = target_player
                        st.session_state.cached_filtered_games = filtered_games
                        st.session_state.cached_stats = stats
                        st.session_state.cached_fen_map = fen_map_all
                        st.session_state.cached_fen_map_white = fen_map_white
                        st.session_state.cached_fen_map_black = fen_map_black
                        st.session_state.cached_repertoire = repertoire_data
                        st.session_state.cached_move_evaluations = move_evals
                        st.session_state.cached_deep_profile = deep_profile
                        st.session_state.cached_profile_lang = current_lang
                        tracker.set_step_done("ready", "Sẵn sàng phân tích!" if current_lang == "vi" else "Ready to analyze!")

                        st.session_state.active_nav_page = "Analyze"
                        st.rerun()

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # Data Preview Card
    if st.session_state.online_pgn_bytes is not None:
        try:
            games_preview = cached_parse_pgn(st.session_state.online_pgn_bytes)
            players_p = extract_players(games_preview)
            primary_p = detect_primary_player(games_preview)

            with st.container(border=True):
                st.markdown(f"#### {t('data_preview_title', lang=current_lang)}")
                dp1, dp2, dp3 = st.columns(3)
                dp1.metric(t("games_detected_label", lang=current_lang), len(games_preview))
                dp2.metric(t("players_detected_label", lang=current_lang), len(players_p))
                dp3.metric(t("primary_player_label", lang=current_lang), primary_p if primary_p else "N/A")

                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

                if st.button(t("btn_start_analysis", lang=current_lang), type="primary", use_container_width=True, key="import_start_analysis_btn"):
                    st.session_state.active_nav_page = "Analyze"
                    st.rerun()
        except Exception as e:
            st.error(f"Lỗi đọc PGN: {e}")


# ==============================================================================
# VIEW 08: SETTINGS PAGE
# ==============================================================================
elif active_page == "Settings":
    PageHeader(t("nav_settings", lang=current_lang), "Cấu hình ứng dụng và tùy chọn hiển thị." if current_lang == "vi" else "App settings and display options.")

    with st.container(border=True):
        st.markdown("#### Giao diện & Ngôn ngữ")
        
        col_lang, col_theme = st.columns(2)
        with col_lang:
            st.markdown(f"**{t('nav_language', lang=current_lang)}**")
            new_lang = st.selectbox(
                "Select Language",
                options=["vi", "en"],
                index=0 if current_lang == "vi" else 1,
                format_func=lambda x: "🇻🇳 Tiếng Việt" if x == "vi" else "🇬🇧 English",
                key="settings_page_lang_selector",
                label_visibility="collapsed"
            )
            if new_lang != current_lang:
                st.session_state.language = new_lang
                st.rerun()

        with col_theme:
            st.markdown("**Chế độ Giao diện (Theme)**")
            st.selectbox(
                "Theme Mode",
                options=["Light (Mặc định)"],
                index=0,
                key="settings_page_theme_selector",
                label_visibility="collapsed"
            )

    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Quản lý Dữ liệu")
        st.caption("Xóa cache dữ liệu hiện tại và reset bàn cờ.")
        if st.button("Xóa Cache Dữ Liệu", icon=":material/delete:", key="reset_cache_btn"):
            st.session_state.online_pgn_bytes = None
            st.session_state.online_pgn_name = ""
            st.session_state.cached_fen_map = {}
            st.session_state.cached_fen_map_white = {}
            st.session_state.cached_fen_map_black = {}
            st.session_state.analysis_color_filter = "all"
            st.session_state.cached_stats = {}
            st.session_state.cached_repertoire = {}
            st.session_state.cached_filtered_games = []
            st.session_state.chess_board.reset()
            st.session_state.move_history = []
            st.session_state.full_analysis_line = []
            st.session_state.active_nav_page = "Import"
            st.success("Đã xóa cache dữ liệu.")
            st.rerun()
