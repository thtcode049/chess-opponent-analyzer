"""
Playing Style Metrics Module (Raw Metrics & Normalization)
---------------------------------------------------------
Chức năng: Định lượng 9 hành vi cờ vua quan sát được từ dữ liệu ván đấu PGN,
python-chess board state và Stockfish evaluations.

Nguyên tắc:
1. Deterministic & Explainable: Mọi metric đều tính toán dựa trên số liệu cụ thể.
2. Separation of Concerns: Chỉ tính raw metrics và chuẩn hóa 0-100, không chứa logic phân loại style hay UI.
3. Cache-friendly: Tái sử dụng dữ liệu move evaluations có sẵn mà không gọi lại Stockfish.
"""

from typing import List, Dict, Any, Optional
import statistics
import chess

from src.analysis.pawn_structure import detect_pawn_structure


def clamp_normalize(val: float, min_val: float, max_val: float) -> float:
    """Chuẩn hóa một giá trị thực về thang điểm 0 - 100 (có kẹp biên)."""
    if max_val <= min_val:
        return 50.0
    normalized = ((val - min_val) / (max_val - min_val)) * 100.0
    return round(max(0.0, min(100.0, normalized)), 1)


def compute_complexity_index(
    filtered_games: List[Dict[str, Any]],
    move_evaluations: Optional[List[Dict[str, Any]]] = None
) -> float:
    """
    METRIC 1: COMPLEXITY INDEX (0-100)
    Định lượng mức độ phức tạp của các position mà kỳ thủ thường thi đấu.
    Dựa trên: số lượng legal moves, forcing moves (checks, captures), và mật độ va chạm quân.
    """
    if not filtered_games:
        return 50.0

    total_positions = 0
    complexity_sum = 0.0

    # Lấy FEN từ move_evaluations nếu có, hoặc replay lại từ filtered_games
    fens_to_check: List[str] = []
    if move_evaluations:
        for ev in move_evaluations:
            fen = ev.get("fen_before", "")
            if fen:
                fens_to_check.append(fen)

    if not fens_to_check:
        for game in filtered_games[:20]:  # Giới hạn 20 ván để đảm bảo performance
            moves = game.get("moves", [])
            board = chess.Board()
            for ply, san in enumerate(moves):
                if 12 <= ply <= 60:  # Giai đoạn trung cuộc phức tạp
                    fens_to_check.append(board.fen())
                try:
                    board.push_san(san)
                except Exception:
                    break

    if not fens_to_check:
        return 50.0

    for fen in fens_to_check:
        try:
            b = chess.Board(fen)
            legal_moves = list(b.legal_moves)
            n_legal = len(legal_moves)
            if n_legal == 0:
                continue

            n_captures = sum(1 for m in legal_moves if b.is_capture(m))
            n_checks = sum(1 for m in legal_moves if b.gives_check(m))
            
            # Điểm phức tạp vị trí = cơ sở legal moves + trọng số nước ép buộc (forcing)
            pos_complexity = (n_legal * 1.0) + (n_captures * 3.5) + (n_checks * 4.5)
            complexity_sum += pos_complexity
            total_positions += 1
        except Exception:
            continue

    if total_positions == 0:
        return 50.0

    avg_complexity = complexity_sum / total_positions
    # Benchmark: vị trí cờ tiêu chuẩn dao động từ 25 (tĩnh, ít đòn) đến 75 (loạn đòn, sắc nét)
    return clamp_normalize(avg_complexity, min_val=25.0, max_val=75.0)


def compute_volatility_score(move_evaluations: Optional[List[Dict[str, Any]]] = None) -> float:
    """
    METRIC 2: EVALUATION VOLATILITY (0-100)
    Đo lường độ biến động điểm số thế cờ từ Stockfish evaluation (abs(delta_eval)).
    """
    if not move_evaluations:
        return 50.0

    all_deltas = [abs(ev.get("delta_eval", 0.0)) for ev in move_evaluations if "delta_eval" in ev]
    if len(all_deltas) < 2:
        return 50.0

    try:
        stdev_val = statistics.stdev(all_deltas)
        # Benchmark: độ lệch chuẩn eval delta dao động từ 0.3 (rất phẳng lặng) đến 2.2 (rất hỗn loạn)
        return clamp_normalize(stdev_val, min_val=0.3, max_val=2.2)
    except Exception:
        return 50.0


def compute_queen_retention_25(filtered_games: List[Dict[str, Any]]) -> float:
    """
    METRIC 3: QUEEN RETENTION AFTER MOVE 25 (0-100)
    % số ván mà Hậu của cả hai bên vẫn còn trên bàn cờ sau nước 25 (ply 50).
    """
    if not filtered_games:
        return 50.0

    games_with_queens_at_25 = 0
    total_valid_games = 0

    for game in filtered_games:
        moves = game.get("moves", [])
        if not moves:
            continue

        total_valid_games += 1
        board = chess.Board()
        queens_present_at_25 = True

        for ply, san in enumerate(moves):
            try:
                board.push_san(san)
            except Exception:
                break

            move_num = (ply // 2) + 1
            if move_num <= 25:
                w_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
                b_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
                if w_queens == 0 or b_queens == 0:
                    queens_present_at_25 = False
                    break

        if queens_present_at_25 and len(moves) >= 20:
            games_with_queens_at_25 += 1

    if total_valid_games == 0:
        return 50.0

    retention_pct = (games_with_queens_at_25 / total_valid_games) * 100.0
    return round(max(0.0, min(100.0, retention_pct)), 1)


def compute_simplification_metrics(filtered_games: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    METRIC 4: SIMPLIFICATION METRICS (0-100)
    Theo dõi tần suất đổi Hậu sớm trước nước 20 và tốc độ đơn giản hóa lực lượng.
    """
    if not filtered_games:
        return {
            "queen_trade_before_20": 30.0,
            "simplification_rate": 40.0
        }

    queen_traded_early_cnt = 0
    rapid_simplification_cnt = 0
    total_games = len(filtered_games)

    for game in filtered_games:
        moves = game.get("moves", [])
        board = chess.Board()
        queen_traded_ply: Optional[int] = None
        minor_major_trades_before_30 = 0

        for ply, san in enumerate(moves):
            try:
                is_cap = ("x" in san)
                board.push_san(san)
            except Exception:
                break

            move_num = (ply // 2) + 1
            w_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
            b_queens = len(board.pieces(chess.QUEEN, chess.BLACK))

            if (w_queens == 0 and b_queens == 0) and queen_traded_ply is None:
                queen_traded_ply = ply

            if is_cap and move_num <= 30:
                minor_major_trades_before_30 += 1

        if queen_traded_ply is not None and queen_traded_ply <= 40:  # Nước 20 = ply 40
            queen_traded_early_cnt += 1

        if minor_major_trades_before_30 >= 6 or (queen_traded_ply is not None and queen_traded_ply <= 30):
            rapid_simplification_cnt += 1

    early_trade_pct = (queen_traded_early_cnt / total_games) * 100.0 if total_games > 0 else 0.0
    simp_rate_pct = (rapid_simplification_cnt / total_games) * 100.0 if total_games > 0 else 0.0

    return {
        "queen_trade_before_20": round(early_trade_pct, 1),
        "simplification_rate": round(simp_rate_pct, 1)
    }


def compute_open_closed_preference(filtered_games: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    METRIC 5: OPEN / CLOSED PREFERENCE (0-100)
    Thống kê tỷ lệ các cấu trúc ván đấu thuộc Open, Semi-Open, Closed.
    """
    if not filtered_games:
        return {
            "open_preference": 33.3,
            "semi_open_preference": 33.3,
            "closed_preference": 33.4
        }

    open_cnt = 0
    semi_open_cnt = 0
    closed_cnt = 0
    total = len(filtered_games)

    for game in filtered_games:
        moves = game.get("moves", [])
        board = chess.Board()
        detected_struct = "Standard"

        for ply, san in enumerate(moves):
            try:
                board.push_san(san)
            except Exception:
                break
            if 14 <= ply <= 28:  # Nước 8 đến 14
                struct_res = detect_pawn_structure(board)
                st_key = struct_res.get("structure", "Standard")
                if st_key in ["Open", "Semi-Open", "Closed", "Carlsbad", "Benoni", "IQP"]:
                    detected_struct = st_key
                    break

        if detected_struct == "Open":
            open_cnt += 1
        elif detected_struct in ["Closed", "Carlsbad", "Benoni"]:
            closed_cnt += 1
        else:
            semi_open_cnt += 1

    return {
        "open_preference": round((open_cnt / total) * 100.0, 1),
        "semi_open_preference": round((semi_open_cnt / total) * 100.0, 1),
        "closed_preference": round((closed_cnt / total) * 100.0, 1)
    }


def compute_prophylaxis_rate(
    filtered_games: List[Dict[str, Any]],
    move_evaluations: Optional[List[Dict[str, Any]]] = None
) -> float:
    """
    METRIC 6: PROPHYLAXIS RATE (0-100)
    Rule-based detection các nước dự phòng (King safety move Kh1/Kb1, defensive wing push h3/a3)
    được Stockfish kiểm chứng (cpl <= 35).
    """
    if not filtered_games:
        return 30.0

    prophylactic_candidates = 0
    total_eligible_moves = 0

    # Index move evaluations theo FEN để tra cứu cpl nhanh
    cpl_by_fen = {}
    if move_evaluations:
        for ev in move_evaluations:
            fen = ev.get("fen_before", "")
            if fen:
                cpl_by_fen[fen] = ev.get("cpl", 0.0)

    for game in filtered_games:
        moves = game.get("moves", [])
        player_color = game.get("player_color", "white").lower()
        board = chess.Board()

        for ply, san in enumerate(moves):
            fen_before = board.fen()
            is_player_turn = (ply % 2 == 0 and player_color == "white") or (ply % 2 == 1 and player_color == "black")
            move_num = (ply // 2) + 1

            try:
                move_obj = board.parse_san(san)
            except Exception:
                break

            if is_player_turn and 10 <= move_num <= 35:
                total_eligible_moves += 1
                san_clean = san.replace("+", "").replace("#", "")
                from_sq = move_obj.from_square
                to_sq = move_obj.to_square
                piece = board.piece_at(from_sq)

                is_capture = board.is_capture(move_obj)
                is_quiet = not is_capture and not board.gives_check(move_obj)

                is_prophylactic_shape = False
                # 1. Di chuyển Vua an toàn / né đòn
                if piece and piece.piece_type == chess.KING and is_quiet:
                    if san_clean in ["Kh1", "Kh8", "Kg1", "Kg8", "Kb1", "Kb8", "Kf1", "Kf8"]:
                        is_prophylactic_shape = True

                # 2. Đẩy Tốt biên phòng thủ ngừa quân đối phương xâm nhập
                elif piece and piece.piece_type == chess.PAWN and is_quiet:
                    to_file = chess.square_file(to_sq)
                    if to_file in [0, 1, 6, 7] and san_clean in ["h3", "h6", "a3", "a6", "g3", "g6", "b3", "b6"]:
                        is_prophylactic_shape = True

                if is_prophylactic_shape:
                    # Kiểm tra Stockfish evaluation nếu có
                    cpl_eval = cpl_by_fen.get(fen_before, 0.0)
                    if cpl_eval <= 35.0:
                        prophylactic_candidates += 1

            board.push(move_obj)

    if total_eligible_moves == 0:
        return 30.0

    raw_rate = (prophylactic_candidates / total_eligible_moves) * 100.0
    # Benchmark: tỷ lệ nước dự phòng thường chiếm từ 4% đến 22% số nước trung cuộc
    return clamp_normalize(raw_rate, min_val=4.0, max_val=22.0)


def compute_resilience_rate(
    filtered_games: List[Dict[str, Any]],
    move_evaluations: Optional[List[Dict[str, Any]]] = None
) -> float:
    """
    METRIC 7: RESILIENCE RATE (0-100)
    Một game đủ điều kiện nếu opponent_eval <= -1.5 ở ít nhất một thời điểm.
    Nếu kết thúc Draw hoặc Win -> resilient game (mỗi game đếm 1 lần duy nhất).
    """
    if not move_evaluations or not filtered_games:
        return 50.0

    games_map: Dict[int, List[Dict[str, Any]]] = {}
    for ev in move_evaluations:
        g_idx = ev.get("game_index", 0)
        games_map.setdefault(g_idx, []).append(ev)

    eligible_games = 0
    resilient_games = 0

    for g_idx, ev_list in games_map.items():
        if g_idx >= len(filtered_games):
            continue
        game = filtered_games[g_idx]
        player_color = game.get("player_color", "white").lower()
        result = game.get("result", "*")

        is_win = (player_color == "white" and result == "1-0") or (player_color == "black" and result == "0-1")
        is_draw = (result == "1/2-1/2")

        min_opp_eval = min([ev.get("eval_after", 0.0) for ev in ev_list], default=0.0)

        # Ngưỡng bị dẫn sâu >= 1.5 pawns
        if min_opp_eval <= -1.5:
            eligible_games += 1
            if is_win or is_draw:
                resilient_games += 1

    if eligible_games == 0:
        return 50.0

    return round((resilient_games / eligible_games) * 100.0, 1)


def compute_counterattack_conversion_rate(
    filtered_games: List[Dict[str, Any]],
    move_evaluations: Optional[List[Dict[str, Any]]] = None
) -> Optional[float]:
    """
    METRIC 8: COUNTERATTACK CONVERSION RATE (0-100 or None)
    Tìm các ván cờ:
    1. opponent_eval bị dẫn sâu <= -1.5
    2. Sau đó có bước ngoặt đảo chiều đánh giá (delta_eval >= +1.5 do đối phương mắc lỗi)
    3. Kỳ thủ cứu hòa hoặc giành chiến thắng.
    Trả về None nếu không có ván nào đủ điều kiện.
    """
    if not move_evaluations or not filtered_games:
        return None

    games_map: Dict[int, List[Dict[str, Any]]] = {}
    for ev in move_evaluations:
        g_idx = ev.get("game_index", 0)
        games_map.setdefault(g_idx, []).append(ev)

    eligible_deficit_games = 0
    counterattack_wins = 0

    for g_idx, ev_list in games_map.items():
        if g_idx >= len(filtered_games):
            continue
        game = filtered_games[g_idx]
        player_color = game.get("player_color", "white").lower()
        result = game.get("result", "*")

        is_win = (player_color == "white" and result == "1-0") or (player_color == "black" and result == "0-1")
        is_draw = (result == "1/2-1/2")

        was_in_deficit = False
        had_turnaround = False

        for ev in ev_list:
            eval_after = ev.get("eval_after", 0.0)
            delta_eval = ev.get("delta_eval", 0.0)

            if eval_after <= -1.5:
                was_in_deficit = True

            # Sau khi bị dẫn, có nước đi đảo chiều lớn >= 1.5 pawns
            if was_in_deficit and delta_eval >= 1.5:
                had_turnaround = True

        if was_in_deficit:
            eligible_deficit_games += 1
            if had_turnaround and (is_win or is_draw):
                counterattack_wins += 1

    if eligible_deficit_games == 0:
        return None

    return round((counterattack_wins / eligible_deficit_games) * 100.0, 1)


def compute_phase_consistency_score(
    filtered_games: List[Dict[str, Any]],
    stats: Dict[str, Any],
    move_evaluations: Optional[List[Dict[str, Any]]] = None,
    phases_data: Optional[Dict[str, Any]] = None
) -> float:
    """
    METRIC 9: PHASE & COLOR CONSISTENCY SCORE (0-100)
    Đo lường tính đồng đều về độ chính xác ACPL giữa 3 giai đoạn (Opening, Middlegame, Endgame),
    kết hợp khoảng cách hiệu suất giữa White vs Black.
    """
    phase_acpls = []
    if phases_data and "phases" in phases_data:
        p_dict = phases_data["phases"]
        for p_key in ["opening", "middlegame", "endgame"]:
            acpl = p_dict.get(p_key, {}).get("avg_acpl")
            if acpl is not None and acpl > 0:
                phase_acpls.append(acpl)

    if len(phase_acpls) >= 2:
        phase_std = statistics.stdev(phase_acpls)
    else:
        phase_std = 15.0  # Mặc định

    w_score = stats.get("white_score_percentage", 50.0)
    b_score = stats.get("black_score_percentage", 50.0)
    color_gap = abs(w_score - b_score)

    # Điểm Phase Consistency: Standard deviation càng thấp -> Điểm càng cao
    norm_phase_consistency = clamp_normalize(35.0 - phase_std, min_val=0.0, max_val=35.0)
    # Điểm Color Balance: Khoảng cách Trắng/Đen càng nhỏ -> Điểm càng cao
    norm_color_balance = clamp_normalize(50.0 - color_gap, min_val=0.0, max_val=50.0)

    combined = (0.65 * norm_phase_consistency) + (0.35 * norm_color_balance)
    return round(max(0.0, min(100.0, combined)), 1)


def extract_all_style_metrics(
    filtered_games: List[Dict[str, Any]],
    stats: Dict[str, Any],
    move_evaluations: Optional[List[Dict[str, Any]]] = None,
    phases_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Tập hợp và trích xuất toàn bộ 9 Raw Metrics.
    """
    complexity = compute_complexity_index(filtered_games, move_evaluations)
    volatility = compute_volatility_score(move_evaluations)
    queen_retention = compute_queen_retention_25(filtered_games)
    simplification_info = compute_simplification_metrics(filtered_games)
    pref_info = compute_open_closed_preference(filtered_games)
    prophylaxis = compute_prophylaxis_rate(filtered_games, move_evaluations)
    resilience = compute_resilience_rate(filtered_games, move_evaluations)
    counterattack = compute_counterattack_conversion_rate(filtered_games, move_evaluations)
    phase_consistency = compute_phase_consistency_score(filtered_games, stats, move_evaluations, phases_data)

    return {
        "complexity_index": complexity,
        "volatility_score": volatility,
        "queen_retention_25": queen_retention,
        "queen_trade_before_20": simplification_info["queen_trade_before_20"],
        "simplification_rate": simplification_info["simplification_rate"],
        "open_preference": pref_info["open_preference"],
        "semi_open_preference": pref_info["semi_open_preference"],
        "closed_preference": pref_info["closed_preference"],
        "prophylaxis_rate": prophylaxis,
        "resilience_rate": resilience,
        "counterattack_conversion_rate": counterattack,
        "phase_consistency_score": phase_consistency,
        "has_engine_data": bool(move_evaluations and len(move_evaluations) > 0)
    }
