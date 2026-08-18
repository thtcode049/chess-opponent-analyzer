"""
Unit Tests for Stockfish Engine Integration & Config
---------------------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import chess
from src.engine.engine_config import find_stockfish_executable, ENGINE_DEPTH
from src.engine.stockfish_engine import StockfishEngine, normalize_score


def test_engine_config():
    assert isinstance(ENGINE_DEPTH, int) and ENGINE_DEPTH > 0
    # Executable path finding should return str or None without throwing
    exe_path = find_stockfish_executable()
    assert exe_path is None or isinstance(exe_path, str)


def test_normalize_score():
    # Test cp score
    class DummyCpScore:
        def is_mate(self):
            return False
        @property
        def relative(self):
            class Rel:
                def score(self, mate_score=1000):
                    return 150
            return Rel()

    norm = normalize_score(DummyCpScore())
    assert norm["cp"] == 150.0
    assert not norm["is_mate"]

    # Test mate score
    class DummyMateScore:
        def is_mate(self):
            return True
        @property
        def relative(self):
            class Rel:
                def mate(self):
                    return 3
            return Rel()

    norm_mate = normalize_score(DummyMateScore())
    assert norm_mate["cp"] == 1000.0
    assert norm_mate["is_mate"]
    assert norm_mate["mate_in"] == 3


def test_stockfish_engine_wrapper_graceful():
    # Test initialization with invalid path gracefully handles without crashing
    engine = StockfishEngine(path="/invalid/path/to/stockfish")
    assert not engine.is_available()
    
    eval_res = engine.evaluate_position(chess.STARTING_FEN)
    assert not eval_res["available"]
    assert eval_res["opponent_eval"] == 0.0

    engine.close()
