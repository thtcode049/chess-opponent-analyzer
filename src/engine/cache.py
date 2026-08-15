"""
Engine Analysis Caching Module
------------------------------
Chức năng: Quản lý bộ nhớ đệm (In-Memory Cache) cho kết quả phân tích của Stockfish.
"""

from typing import Dict, Any, Optional

_ENGINE_EVAL_CACHE: Dict[str, Dict[str, Any]] = {}


def get_cached_evaluation(fen: str, depth: int, opponent_color: str) -> Optional[Dict[str, Any]]:
    cache_key = f"{fen}_{depth}_{opponent_color}"
    return _ENGINE_EVAL_CACHE.get(cache_key)


def set_cached_evaluation(fen: str, depth: int, opponent_color: str, result: Dict[str, Any]):
    cache_key = f"{fen}_{depth}_{opponent_color}"
    _ENGINE_EVAL_CACHE[cache_key] = result


def clear_engine_cache():
    _ENGINE_EVAL_CACHE.clear()
