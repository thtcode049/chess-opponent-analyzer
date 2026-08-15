from pathlib import Path
import chess
from src.pgn_parser import parse_pgn, filter_games_by_player
from src.opening_tree import build_opening_tree, get_position_details


def test_build_opening_tree_starting_position():
    sample_path = Path("data/sample.pgn")
    games = parse_pgn(sample_path)
    nep_games = filter_games_by_player(games, "Nepomniachtchi, Ian")
    
    root, fen_map = build_opening_tree(nep_games)
    start_fen = chess.Board().fen()
    
    assert start_fen in fen_map
    assert fen_map[start_fen].games_count == 2
    assert root.games_count == 2


def test_opening_tree_continuations_stats():
    sample_path = Path("data/sample.pgn")
    games = parse_pgn(sample_path)
    nep_games = filter_games_by_player(games, "Nepomniachtchi, Ian")
    
    root, fen_map = build_opening_tree(nep_games)
    start_fen = chess.Board().fen()
    details = get_position_details(fen_map, start_fen)
    
    assert details["in_pgn"] is True
    assert details["total_games"] == 2
    assert len(details["continuations"]) > 0

    total_usage = sum(c["usage_pct"] for c in details["continuations"])
    assert abs(total_usage - 100.0) < 0.1


def test_position_not_in_pgn():
    fen_map = {}
    random_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
    details = get_position_details(fen_map, random_fen)
    
    assert details["in_pgn"] is False
    assert details["total_games"] == 0
    assert details["score_pct"] == 0.0
    assert len(details["continuations"]) == 0


def test_single_game_info_extraction():
    dummy_games = [
        {
            "white": "PlayerA",
            "white_elo": 2000,
            "black": "PlayerB",
            "black_elo": 1900,
            "result": "1-0",
            "site": "https://lichess.org/test1234",
            "moves": ["e4", "e5", "Nf3"],
            "player_color": "white",
            "opening": "King's Knight Opening",
        }
    ]
    root, fen_map = build_opening_tree(dummy_games)
    start_fen = chess.Board().fen()
    details = get_position_details(fen_map, start_fen)
    
    assert len(details["continuations"]) == 1
    cont = details["continuations"][0]
    assert cont["games_count"] == 1
    assert cont["single_game_info"] is not None
    assert cont["single_game_info"]["white"] == "PlayerA"
    assert cont["single_game_info"]["black"] == "PlayerB"
    assert cont["single_game_info"]["result"] == "1-0"


def test_find_common_move_prefix():
    from app import find_common_move_prefix
    
    games = [
        {"moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"]},
        {"moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6"]},
        {"moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Be7"]},
    ]
    prefix = find_common_move_prefix(games)
    assert prefix == ["e4", "e5", "Nf3", "Nc6", "Bc4"]


def test_find_representative_line_transposition():
    from app import find_representative_line_for_games

    # Transposition example: Dutch Defense played via different valid move orders
    games = [
        {"moves": ["d4", "f5", "c4", "Nf6", "g3", "e6"]},
        {"moves": ["d4", "f5", "c4", "Nf6", "g3", "g6"]},
        {"moves": ["d4", "e6", "c4", "f5", "g3", "Nf6"]},
        {"moves": ["d4", "e6", "c4", "f5", "g3", "Nf6"]},
    ]
    rep_line = find_representative_line_for_games(games)
    # The canonical position reached by all 4 games is after 5 plies (d4, f5, c4, Nf6, g3)
    assert len(rep_line) >= 5
    # Check that representative line is one of the valid move paths
    assert rep_line[:5] in [["d4", "f5", "c4", "Nf6", "g3"], ["d4", "e6", "c4", "f5", "g3"]]


def test_push_move_preserves_full_analysis_line():
    import streamlit as st
    import chess
    from app import push_move, pop_move, step_next

    st.session_state.chess_board = chess.Board()
    st.session_state.move_history = []
    st.session_state.full_analysis_line = ["e4", "e5", "Nf3", "Nc6", "Bc4"]

    # Play e4
    push_move("e4")
    assert st.session_state.move_history == ["e4"]
    assert st.session_state.full_analysis_line == ["e4", "e5", "Nf3", "Nc6", "Bc4"]

    # Pop move back to start
    pop_move()
    assert st.session_state.move_history == []
    assert st.session_state.full_analysis_line == ["e4", "e5", "Nf3", "Nc6", "Bc4"]

    # Step next twice
    step_next()
    step_next()
    assert st.session_state.move_history == ["e4", "e5"]
    assert st.session_state.full_analysis_line == ["e4", "e5", "Nf3", "Nc6", "Bc4"]


