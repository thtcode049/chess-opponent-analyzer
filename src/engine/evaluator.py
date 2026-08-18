"""
Engine Evaluator Module
-----------------------
Chức năng: Thực hiện phân tích chuỗi nước đi ván đấu bằng Stockfish.
Tính toán ACPL (Average Centipawn Loss), Delta Eval, và lưu trữ dữ liệu phân tích dạng cấu trúc.
"""

from typing import List, Dict, Any, Optional
import chess

from src.engine.stockfish_engine import StockfishEngine


def analyze_game_moves(
    game: Dict[str, Any],
    engine: StockfishEngine,
    depth: int = 6
) -> List[Dict[str, Any]]:
    """
    Phân tích từng nước đi của KỲ THỦ ĐỐI THỦ trong một ván đấu.
    """
    if not engine.is_available():
        return []

    moves = game.get("moves", [])
    player_color = game.get("player_color", "white").lower()
    if not moves:
        return []

    results = []
    board = chess.Board()

    for ply, san_move in enumerate(moves):
        fen_before = board.fen()
        try:
            move_obj = board.parse_san(san_move)
        except Exception:
            break

        move_color = "white" if ply % 2 == 0 else "black"
        is_opponent_move = (move_color == player_color)

        if is_opponent_move:
            analysis = engine.analyze_move(
                fen_before=fen_before,
                move_san=san_move,
                depth=depth,
                opponent_color=player_color
            )
            if analysis.get("available"):
                move_num = (ply // 2) + 1
                analysis["ply"] = ply
                analysis["move_number"] = move_num
                results.append(analysis)

        board.push(move_obj)

    return results


def batch_analyze_games(
    games: List[Dict[str, Any]],
    engine: StockfishEngine,
    max_games: int = 10,
    depth: int = 6
) -> Dict[str, Any]:
    """
    Thực hiện phân tích Batch siêu tốc trên danh sách ván đấu chọn lọc (mặc định 10 ván).
    """
    if not engine.is_available() or not games:
        for g in (games or []):
            g.setdefault("game_acpl", None)
            g.setdefault("analyzed_moves", 0)
        return {
            "available": False,
            "analyzed_games": 0,
            "total_moves_analyzed": 0,
            "overall_acpl": None,
            "move_evaluations": [],
            "game_summaries": []
        }

    selected_games = games[:max_games]
    all_evaluations = []
    game_summaries = []

    for idx, g in enumerate(selected_games):
        evals = analyze_game_moves(g, engine, depth=depth)
        if not evals:
            g["game_acpl"] = None
            g["analyzed_moves"] = 0
            continue

        cpls = [e["cpl"] for e in evals if "cpl" in e]
        game_acpl = round(sum(cpls) / len(cpls), 1) if cpls else None

        g["game_acpl"] = game_acpl
        g["analyzed_moves"] = len(evals)

        game_summaries.append({
            "game_index": idx,
            "opening": g.get("opening", "Unknown"),
            "result": g.get("result", "*"),
            "player_color": g.get("player_color", "white"),
            "moves_analyzed": len(evals),
            "game_acpl": game_acpl,
            "avg_cpl": game_acpl if game_acpl is not None else 0.0,
            "site": g.get("site", "")
        })

        for e in evals:
            e["game_index"] = idx
            e["game_opening"] = g.get("opening", "Unknown")
            e["site"] = g.get("site", "")
            all_evaluations.append(e)

    # Đảm bảo các games còn lại (nếu có) có default None
    for g in games[max_games:]:
        g.setdefault("game_acpl", None)
        g.setdefault("analyzed_moves", 0)

    total_moves = len(all_evaluations)
    all_cpls = [e["cpl"] for e in all_evaluations if "cpl" in e]
    overall_acpl = round(sum(all_cpls) / len(all_cpls), 1) if all_cpls else None

    return {
        "available": True,
        "analyzed_games": len(game_summaries),
        "total_moves_analyzed": total_moves,
        "overall_acpl": overall_acpl,
        "move_evaluations": all_evaluations,
        "game_summaries": game_summaries
    }
