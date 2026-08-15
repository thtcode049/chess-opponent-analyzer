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
    depth: int = 12
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
    max_games: int = 15,
    depth: int = 12
) -> Dict[str, Any]:
    """
    Thực hiện phân tích Batch trên danh sách ván đấu chọn lọc.
    """
    if not engine.is_available() or not games:
        return {
            "available": False,
            "analyzed_games": 0,
            "total_moves_analyzed": 0,
            "move_evaluations": [],
            "game_summaries": []
        }

    selected_games = games[:max_games]
    all_evaluations = []
    game_summaries = []

    for idx, g in enumerate(selected_games):
        evals = analyze_game_moves(g, engine, depth=depth)
        if not evals:
            continue

        cpls = [e["cpl"] for e in evals if "cpl" in e]
        avg_cpl = sum(cpls) / len(cpls) if cpls else 0.0

        game_summaries.append({
            "game_index": idx,
            "opening": g.get("opening", "Unknown"),
            "result": g.get("result", "*"),
            "player_color": g.get("player_color", "white"),
            "moves_analyzed": len(evals),
            "avg_cpl": round(avg_cpl, 1),
            "site": g.get("site", "")
        })

        for e in evals:
            e["game_index"] = idx
            e["game_opening"] = g.get("opening", "Unknown")
            e["site"] = g.get("site", "")
            all_evaluations.append(e)

    total_moves = len(all_evaluations)
    return {
        "available": True,
        "analyzed_games": len(game_summaries),
        "total_moves_analyzed": total_moves,
        "move_evaluations": all_evaluations,
        "game_summaries": game_summaries
    }
