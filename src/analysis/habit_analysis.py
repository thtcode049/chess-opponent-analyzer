"""
Middlegame Habit Analysis Module (Moves 12–25)
-----------------------------------------------
Chức năng: Quan sát và phân loại các thói quen thi đấu ở giai đoạn Trung cuộc (nước 12–25).
Phân loại các xu hướng di chuyển: Hành động Tốt trung tâm, Đẩy Tốt biên, Đổi quân, Cải thiện vị trí quân, An toàn Vua.
"""

from typing import List, Dict, Any
import chess

from src.analysis.confidence import format_confidence_label


def analyze_middlegame_habits(
    filtered_games: List[Dict[str, Any]],
    lang: str = "vi"
) -> Dict[str, Any]:
    """
    Phân tích hành vi nước đi từ nước 12 đến 25 của đối thủ.
    """
    total_moves_observed = 0
    categories = {
        "central_pawn_action": 0,
        "pawn_advance": 0,
        "exchanges": 0,
        "piece_improvement": 0,
        "king_safety": 0,
        "other": 0
    }

    for game in filtered_games:
        moves = game.get("moves", [])
        player_color = game.get("player_color", "white").lower()
        board = chess.Board()

        for ply, san in enumerate(moves):
            fen_before = board.fen()
            try:
                move_obj = board.parse_san(san)
            except Exception:
                break

            move_color = "white" if ply % 2 == 0 else "black"
            move_num = (ply // 2) + 1

            if move_color == player_color and 12 <= move_num <= 25:
                total_moves_observed += 1
                from_sq = move_obj.from_square
                to_sq = move_obj.to_square
                piece = board.piece_at(from_sq)

                is_capture = board.is_capture(move_obj)
                from_file = chess.square_file(from_sq)
                to_file = chess.square_file(to_sq)

                if piece and piece.piece_type == chess.PAWN:
                    if to_file in [2, 3, 4]:  # c, d, e files
                        categories["central_pawn_action"] += 1
                    else:
                        categories["pawn_advance"] += 1
                elif is_capture:
                    categories["exchanges"] += 1
                elif piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    categories["piece_improvement"] += 1
                elif piece and piece.piece_type == chess.KING:
                    categories["king_safety"] += 1
                else:
                    categories["other"] += 1

            board.push(move_obj)

    if total_moves_observed == 0:
        return {
            "total_moves_observed": 0,
            "percentages": {},
            "top_habit": "N/A",
            "observation": "Không đủ dữ liệu nước 12-25" if lang == "vi" else "Insufficient data for moves 12-25",
            "confidence": format_confidence_label(0, lang=lang)
        }

    pcts = {k: round((v / total_moves_observed) * 100, 1) for k, v in categories.items()}

    # Tìm habit hàng đầu
    sorted_habits = sorted(pcts.items(), key=lambda x: x[1], reverse=True)
    top_habit_key, top_pct = sorted_habits[0] if sorted_habits else ("other", 0)

    observations_map = {
        "central_pawn_action": "Thường xuyên giao chiến Tốt ở trung tâm (cột c, d, e)." if lang == "vi" else "Frequent central pawn action in the middlegame.",
        "pawn_advance": "Thường xuyên đẩy Tốt cánh dâng cao công thủ trong trung cuộc." if lang == "vi" else "Frequent wing pawn pushes during moves 12-25.",
        "exchanges": "Thường xuyên chủ động đổi quân để làm gọn hình cờ." if lang == "vi" else "Tends to initiate piece exchanges in the middlegame.",
        "piece_improvement": "Tập trung điều quân nâng cao vị trí các quân cờ nhẹ/nặng." if lang == "vi" else "Focuses on piece development and square improvement.",
        "king_safety": "Ưu tiên củng cố an toàn Vua trong trung cuộc." if lang == "vi" else "Prioritizes king safety during moves 12-25.",
        "other": "Lối chơi linh hoạt đa dạng." if lang == "vi" else "Flexible middlegame approach."
    }

    conf = format_confidence_label(len(filtered_games), lang=lang)

    return {
        "total_moves_observed": total_moves_observed,
        "percentages": pcts,
        "top_habit": top_habit_key,
        "top_pct": top_pct,
        "observation": observations_map.get(top_habit_key, ""),
        "confidence": conf
    }
