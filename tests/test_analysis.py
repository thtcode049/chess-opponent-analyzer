"""
Unit Tests for Deep Analytics Modules
-------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import chess

from src.analysis.phase_analysis import classify_phase, analyze_phase_performance
from src.analysis.pawn_structure import detect_pawn_structure, analyze_structural_performance
from src.analysis.game_dynamics import analyze_game_dynamics
from src.analysis.simplification import analyze_simplification_performance
from src.analysis.habit_analysis import analyze_middlegame_habits
from src.analysis.confidence import get_confidence_level
from src.match_prep import generate_actionable_match_preparation


def test_confidence_level():
    assert get_confidence_level(12) == "HIGH"
    assert get_confidence_level(7) == "MEDIUM"
    assert get_confidence_level(3) == "LOW"


def test_classify_phase():
    board = chess.Board()
    # Move 5 is Opening
    assert classify_phase(board, 5) == "opening"
    # Move 18 with starting pieces is Middlegame
    assert classify_phase(board, 18) == "middlegame"
    # Move 35 is Endgame
    assert classify_phase(board, 35) == "endgame"

    # Empty board material except kings is Endgame
    empty_board = chess.Board("8/8/8/4k3/4K3/8/8/8 w - - 0 1")
    assert classify_phase(empty_board, 15) == "endgame"


def test_detect_pawn_structure():
    # Starting board structure is Symmetrical/Standard
    board = chess.Board()
    res = detect_pawn_structure(board)
    assert "structure" in res

    # IQP position (White pawn d4, no c/e pawns for White)
    iqp_board = chess.Board("r1bqk2r/pp3ppp/2n5/3p4/3P4/5N2/PP1Q1PPP/R3KB1R w KQkq - 0 10")
    res_iqp = detect_pawn_structure(iqp_board)
    assert res_iqp["structure"] == "IQP"


def test_analyze_game_dynamics():
    games = [
        {"player_color": "white", "result": "1/2-1/2"},
        {"player_color": "white", "result": "0-1"},
    ]
    # Game 0 reached opp_eval = +2.5 but ended in Draw (Throw)
    # Game 1 reached opp_eval = -2.5 but ended in Loss (Not resilient)
    evals = [
        {"game_index": 0, "eval_after": 2.5, "delta_eval": 0.5},
        {"game_index": 1, "eval_after": -2.5, "delta_eval": -0.8},
    ]

    dyn = analyze_game_dynamics(games, move_evaluations=evals)
    assert dyn["available"]
    assert dyn["eligible_advantage_games"] == 1
    assert dyn["throw_games"] == 1
    assert dyn["throw_rate"] == 100.0


def test_actionable_match_preparation():
    deep_profile = {
        "repertoire": {
            "all_openings": [{"name": "Sicilian Defense", "games_count": 10, "score_pct": 70.0}],
            "black_repertoire": [{"name": "Sicilian Defense", "games_count": 10, "score_pct": 70.0}]
        },
        "structures": {
            "target_structure": {"name": "IQP", "score_pct": 30.0, "games_count": 8, "confidence": {"label": "Medium"}}
        },
        "phases": {
            "weakest_phase": {"phase": "endgame", "avg_acpl": 55.0}
        },
        "dynamics": {
            "throw_rate": 40.0,
            "resilience_rate": 10.0
        },
        "critical_positions": []
    }

    action_prep = generate_actionable_match_preparation(deep_profile, user_color="white")
    assert "play_plan" in action_prep
    assert "target_plan" in action_prep
    assert "avoid_plan" in action_prep
    assert len(action_prep["play_plan"]) > 0
    assert len(action_prep["target_plan"]) > 0
