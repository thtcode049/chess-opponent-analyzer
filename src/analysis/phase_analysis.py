"""
Game Phase Classification & Performance Analysis Module
-------------------------------------------------------
Chức năng: Phân loại giai đoạn ván đấu (Opening, Middlegame, Endgame) và đo lường độ chính xác (ACPL) từng giai đoạn.
"""

import math
from typing import List, Dict, Any, Optional
import chess

from src.analysis.confidence import format_confidence_label


def calculate_phase_accuracy(avg_acpl: float) -> float:
    """Tính tỷ lệ chính xác Accuracy % từ mức centipawn loss trung bình (ACPL)."""
    if avg_acpl <= 0:
        return 100.0
    acc = 100.0 * math.exp(-0.005 * avg_acpl)
    return round(max(0.0, min(100.0, acc)), 1)


def classify_phase(board: chess.Board, move_number: int) -> str:
    if move_number <= 12:
        return "opening"

    piece_values = {
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }
    total_material = 0
    for sq, piece in board.piece_map().items():
        if piece.piece_type in piece_values:
            total_material += piece_values[piece.piece_type]

    if total_material <= 14 or move_number >= 31:
        return "endgame"

    return "middlegame"


def analyze_phase_performance(
    filtered_games: List[Dict[str, Any]],
    move_evaluations: Optional[List[Dict[str, Any]]] = None,
    lang: str = "vi"
) -> Dict[str, Any]:
    phases_data = {
        "opening": {"moves_count": 0, "cpls": [], "mistakes": 0, "games": set()},
        "middlegame": {"moves_count": 0, "cpls": [], "mistakes": 0, "games": set()},
        "endgame": {"moves_count": 0, "cpls": [], "mistakes": 0, "games": set()}
    }

    if move_evaluations:
        for ev in move_evaluations:
            fen = ev.get("fen_before", "")
            move_num = ev.get("move_number", 1)
            cpl = ev.get("cpl", 0.0)
            g_idx = ev.get("game_index", 0)

            board = chess.Board(fen) if fen else chess.Board()
            phase = classify_phase(board, move_num)

            phases_data[phase]["moves_count"] += 1
            phases_data[phase]["cpls"].append(cpl)
            phases_data[phase]["games"].add(g_idx)
            if cpl >= 100.0:
                phases_data[phase]["mistakes"] += 1
    else:
        # Fallback: Phân loại giai đoạn và đếm số nước từ danh sách ván đấu
        for g_idx, game in enumerate(filtered_games or []):
            moves = game.get("moves", [])
            if not moves:
                continue
            board = chess.Board()
            for ply, san in enumerate(moves):
                try:
                    move_num = (ply // 2) + 1
                    phase = classify_phase(board, move_num)
                    phases_data[phase]["moves_count"] += 1
                    phases_data[phase]["games"].add(g_idx)
                    move_obj = board.parse_san(san)
                    board.push(move_obj)
                except Exception:
                    break

    summary = {}
    for phase_name in ["opening", "middlegame", "endgame"]:
        data = phases_data[phase_name]
        cpls = data["cpls"]
        avg_acpl = round(sum(cpls) / len(cpls), 1) if cpls else 0.0
        accuracy_pct = calculate_phase_accuracy(avg_acpl) if cpls else None

        sorted_cpls = sorted(cpls)
        n = len(sorted_cpls)
        median_acpl = round(sorted_cpls[n // 2], 1) if n > 0 else 0.0

        sample_games = len(data["games"])
        conf = format_confidence_label(sample_games, lang=lang)

        summary[phase_name] = {
            "phase": phase_name,
            "games_count": sample_games,
            "moves_count": data["moves_count"],
            "avg_acpl": avg_acpl if cpls else 0.0,
            "median_acpl": median_acpl,
            "mistakes_count": data["mistakes"],
            "accuracy_pct": accuracy_pct,
            "confidence": conf
        }

    valid_phases = [p for p in summary.values() if p["moves_count"] >= 5]
    weakest_phase = max(valid_phases, key=lambda x: x["avg_acpl"]) if valid_phases else summary["middlegame"]
    best_phase = min(valid_phases, key=lambda x: x["avg_acpl"]) if valid_phases else summary["opening"]

    return {
        "phases": summary,
        "weakest_phase": weakest_phase,
        "best_phase": best_phase
    }
