"""
Unit Tests for Playing Style Profile Module
-------------------------------------------
Tests 9 raw metrics, 4 independent style scores, normalization,
primary/secondary classification, confidence rating, evidence generation, and edge cases.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import chess

from src.analysis.style_metrics import (
    clamp_normalize,
    compute_complexity_index,
    compute_volatility_score,
    compute_queen_retention_25,
    compute_simplification_metrics,
    compute_open_closed_preference,
    compute_prophylaxis_rate,
    compute_resilience_rate,
    compute_counterattack_conversion_rate,
    compute_phase_consistency_score,
    extract_all_style_metrics
)
from src.analysis.style_classifier import (
    calculate_style_scores,
    determine_primary_and_secondary_style,
    generate_style_evidence,
    classify_player_style
)
from src.player_profile import generate_deep_opponent_profile


def test_clamp_normalization():
    assert clamp_normalize(50, 0, 100) == 50.0
    assert clamp_normalize(-10, 0, 100) == 0.0
    assert clamp_normalize(150, 0, 100) == 100.0
    assert clamp_normalize(10, 10, 10) == 50.0  # Zero division guard


def test_complexity_index():
    # Empty games fallback
    assert compute_complexity_index([]) == 50.0

    # Games with sharp tactical moves
    games = [{
        "moves": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6", "Bg5", "e6", "f4", "Qb6"],
        "player_color": "white"
    }]
    comp = compute_complexity_index(games)
    assert 0.0 <= comp <= 100.0


def test_volatility_score():
    # No engine data
    assert compute_volatility_score(None) == 50.0
    assert compute_volatility_score([]) == 50.0

    # Flat evaluation (low volatility)
    flat_evals = [{"delta_eval": 0.05}, {"delta_eval": 0.02}, {"delta_eval": 0.04}, {"delta_eval": 0.03}]
    flat_vol = compute_volatility_score(flat_evals)

    # Wild evaluation swings (high volatility)
    wild_evals = [{"delta_eval": 3.5}, {"delta_eval": -2.8}, {"delta_eval": 4.0}, {"delta_eval": -1.9}]
    wild_vol = compute_volatility_score(wild_evals)

    assert wild_vol > flat_vol


def test_queen_retention_25():
    # Game where queens traded on move 4
    early_trade_game = {
        "moves": ["e4", "e5", "d4", "exd4", "Qxd4", "Nc6", "Qxg7", "Qf6", "Qxf6", "Nxf6"],
        "player_color": "white"
    }
    # Game where queens stay on board for 30 moves
    long_game_moves = [
        "e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7",
        "Re1", "b5", "Bb3", "d6", "c3", "O-O", "h3", "Nb8", "d4", "Nbd7",
        "c4", "c6", "cxb5", "axb5", "Nc3", "Bb7", "Bg5", "h6", "Bh4", "Re8",
        "Qd2", "Qb8", "Rad1", "Bf8", "a3", "Qa7", "Ba2", "Rad8", "Qc2", "Qb6",
        "dxe5", "dxe5", "Rd2", "Be7", "Red1", "Qc7", "Bg3", "Bf8", "Nh4", "Nc5"
    ]
    long_game = {"moves": long_game_moves, "player_color": "white"}

    ret_early = compute_queen_retention_25([early_trade_game])
    ret_long = compute_queen_retention_25([long_game])

    assert ret_early == 0.0
    assert ret_long == 100.0


def test_simplification_metrics():
    early_trade_game = {
        "moves": ["e4", "e5", "d4", "exd4", "Qxd4", "Nc6", "Qxg7", "Qf6", "Qxf6", "Nxf6"],
        "player_color": "white"
    }
    simp = compute_simplification_metrics([early_trade_game])
    assert simp["queen_trade_before_20"] == 100.0


def test_open_closed_preference():
    open_game = {
        "moves": ["e4", "e5", "Nf3", "Nc6", "d4", "exd4", "c3", "dxc3", "Bc4", "cxb2", "Bxb2", "d6", "O-O", "Nf6"],
        "player_color": "white"
    }
    closed_game = {
        "moves": ["d4", "d5", "c4", "c6", "Nf3", "Nf6", "e3", "e6", "Nbd2", "Nbd7", "Bd3", "Bd6", "O-O", "O-O"],
        "player_color": "white"
    }
    pref = compute_open_closed_preference([open_game, closed_game])
    assert pref["open_preference"] >= 0.0
    assert pref["closed_preference"] >= 0.0
    assert round(pref["open_preference"] + pref["semi_open_preference"] + pref["closed_preference"]) == 100.0


def test_prophylaxis_rate():
    games = [{
        "moves": [
            "e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6",
            "Be3", "e5", "Nb3", "Be6", "f3", "Be7", "Qd2", "O-O", "O-O-O", "Nbd7",
            "g4", "b5", "Kb1", "Nb6", "h4", "Rc8", "h5", "b4", "Nd5", "Nbxd5",
            "exd5", "Nxd5", "Bf2", "a5", "Bd3", "a4", "Nc1", "Nf4", "Be4", "d5"
        ],
        "player_color": "white"
    }]
    evals = [
        {"fen_before": "r1bq1rk1/1p2bppp/p1np1n2/4p3/4P3/1NN1BP2/PPPQ2PP/2KR1B1R b - - 1 11", "cpl": 10.0}
    ]
    proph = compute_prophylaxis_rate(games, evals)
    assert 0.0 <= proph <= 100.0


def test_resilience_rate():
    games = [
        {"player_color": "white", "result": "1-0"},     # Deficit -> Won (Resilient)
        {"player_color": "white", "result": "1/2-1/2"}, # Deficit -> Drew (Resilient)
        {"player_color": "white", "result": "0-1"}      # Deficit -> Lost (Not resilient)
    ]
    evals = [
        {"game_index": 0, "eval_after": -2.2},
        {"game_index": 1, "eval_after": -1.8},
        {"game_index": 2, "eval_after": -3.0}
    ]
    resil = compute_resilience_rate(games, evals)
    assert resil == round((2 / 3) * 100.0, 1)


def test_counterattack_conversion():
    games = [
        {"player_color": "white", "result": "1-0"},
        {"player_color": "white", "result": "0-1"}
    ]
    evals = [
        {"game_index": 0, "eval_after": -2.0, "delta_eval": -0.5},
        {"game_index": 0, "eval_after": 0.5, "delta_eval": 2.5},   # Turnaround and won
        {"game_index": 1, "eval_after": -2.5, "delta_eval": -0.8}  # Deficit and lost
    ]
    ca = compute_counterattack_conversion_rate(games, evals)
    assert ca == 50.0

    # When no deficit games exist
    assert compute_counterattack_conversion_rate([], None) is None


def test_phase_consistency_score():
    phases_data_uniform = {
        "phases": {
            "opening": {"avg_acpl": 22.0},
            "middlegame": {"avg_acpl": 24.0},
            "endgame": {"avg_acpl": 25.0}
        }
    }
    stats_balanced = {"white_score_percentage": 52.0, "black_score_percentage": 50.0}
    score_uniform = compute_phase_consistency_score([], stats_balanced, None, phases_data_uniform)

    phases_data_wild = {
        "phases": {
            "opening": {"avg_acpl": 10.0},
            "middlegame": {"avg_acpl": 65.0},
            "endgame": {"avg_acpl": 120.0}
        }
    }
    stats_skewed = {"white_score_percentage": 85.0, "black_score_percentage": 25.0}
    score_wild = compute_phase_consistency_score([], stats_skewed, None, phases_data_wild)

    assert score_uniform > score_wild


def test_style_scores_calculation():
    tactical_metrics = {
        "complexity_index": 85.0,
        "volatility_score": 80.0,
        "queen_retention_25": 85.0,
        "open_preference": 75.0,
        "prophylaxis_rate": 15.0,
        "closed_preference": 10.0,
        "simplification_rate": 20.0,
        "resilience_rate": 40.0,
        "counterattack_conversion_rate": 30.0,
        "phase_consistency_score": 50.0
    }
    scores = calculate_style_scores(tactical_metrics)
    assert scores["tactical"] > scores["positional"]
    assert scores["tactical"] > scores["solid"]


def test_primary_secondary_and_confidence():
    scores = {
        "tactical": 82.0,
        "universal": 68.0,
        "positional": 45.0,
        "solid": 38.0
    }
    res_high = determine_primary_and_secondary_style(scores, sample_size=15, lang="vi")
    assert res_high["primary_key"] == "tactical"
    assert res_high["secondary_key"] == "universal"
    assert res_high["confidence_level"] == "HIGH"

    # Small separation
    scores_close = {
        "tactical": 52.0,
        "universal": 51.0,
        "positional": 50.0,
        "solid": 49.0
    }
    res_low = determine_primary_and_secondary_style(scores_close, sample_size=3, lang="vi")
    assert res_low["confidence_level"] == "LOW"


def test_evidence_generation():
    raw_m = {
        "complexity_index": 80.0,
        "volatility_score": 75.0,
        "queen_retention_25": 78.0,
        "closed_preference": 20.0,
        "open_preference": 70.0,
        "resilience_rate": 65.0,
        "phase_consistency_score": 72.0,
        "simplification_rate": 25.0
    }
    evidence_vi = generate_style_evidence(raw_m, lang="vi")
    assert len(evidence_vi) >= 3
    assert any("phức tạp" in ev for ev in evidence_vi)
    assert any("Hậu" in ev for ev in evidence_vi)

    evidence_en = generate_style_evidence(raw_m, lang="en")
    assert len(evidence_en) >= 3
    assert any("complexity" in ev.lower() for ev in evidence_en)


def test_classify_player_style_end_to_end():
    raw_m = extract_all_style_metrics([], {}, None, None)
    profile = classify_player_style(raw_m, sample_size=5, lang="vi")

    assert "scores" in profile
    assert "primary_style" in profile
    assert "secondary_style" in profile
    assert "confidence" in profile
    assert "evidence" in profile
    assert len(profile["evidence"]) >= 1


def test_deep_opponent_profile_integration():
    games = [{
        "moves": ["e4", "e5", "Nf3", "Nc6"],
        "player_color": "white",
        "result": "1-0",
        "white": "Player A",
        "black": "Player B",
        "opening": "King's Pawn Game"
    }]
    stats = {"white_score_percentage": 100.0, "black_score_percentage": 0.0}
    deep_prof = generate_deep_opponent_profile(games, stats, move_evaluations=None, lang="vi")

    assert "style_profile" in deep_prof
    assert "scores" in deep_prof["style_profile"]
    assert "primary_style" in deep_prof["style_profile"]
