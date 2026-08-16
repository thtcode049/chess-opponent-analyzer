"""
Match Preparation & Strategic Recommendations Module
---------------------------------------------------
Chức năng: Phân tích điểm yếu và tự động tạo đề xuất chiến thuật thi đấu (Rule-Based Logic)
giúp người chơi chuẩn bị trước trận đấu đối đầu với một đối thủ cụ thể.
"""

from typing import List, Dict, Any
from src.i18n import t


def analyze_opponent_responses(
    filtered_games: List[Dict[str, Any]],
    user_color: str = "white",
    chosen_move: str = "ALL"
) -> Dict[str, Any]:
    """
    Phân tích phản ứng của đối thủ đối với từng nước đi khai cuộc do người chơi chủ động lựa chọn.
    """
    first_move_groups: Dict[str, Dict[str, Any]] = {}

    target_player_color = "black" if user_color == "white" else "white"
    relevant_games = [g for g in filtered_games if g.get("player_color") == target_player_color]

    for game in relevant_games:
        moves = game.get("moves", [])
        if not moves:
            continue
        
        first_move = moves[0]
        resp_move = moves[1] if len(moves) >= 2 else "Unknown"
        opening_name = game.get("opening", "Unknown Opening")
        result = game.get("result", "*")

        if result == "1/2-1/2":
            is_win, is_draw, is_loss = False, True, False
        elif (target_player_color == "white" and result == "1-0") or (target_player_color == "black" and result == "0-1"):
            is_win, is_draw, is_loss = True, False, False
        else:
            is_win, is_draw, is_loss = False, False, True

        if first_move not in first_move_groups:
            first_move_groups[first_move] = {
                "total_games": 0,
                "responses": {}
            }

        group = first_move_groups[first_move]
        group["total_games"] += 1

        if resp_move not in group["responses"]:
            group["responses"][resp_move] = {
                "resp_move": resp_move,
                "opening_name": opening_name,
                "games_count": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
            }

        r_stat = group["responses"][resp_move]
        r_stat["games_count"] += 1
        if is_win:
            r_stat["wins"] += 1
        elif is_draw:
            r_stat["draws"] += 1
        elif is_loss:
            r_stat["losses"] += 1

    move_options = sorted(first_move_groups.keys(), key=lambda k: first_move_groups[k]["total_games"], reverse=True)
    
    selected_first_move = chosen_move if (chosen_move and chosen_move in first_move_groups) else (move_options[0] if move_options else "e4")

    active_group = first_move_groups.get(selected_first_move, {"total_games": 0, "responses": {}})
    total_in_group = active_group.get("total_games", 0)

    responses_list = []
    for resp_move, data in active_group.get("responses", {}).items():
        g_count = data["games_count"]
        w, d, l = data["wins"], data["draws"], data["losses"]
        score_pct = round(((w + 0.5 * d) / g_count) * 100, 1) if g_count > 0 else 0.0
        usage_pct = round((g_count / total_in_group) * 100, 1) if total_in_group > 0 else 0.0

        if score_pct <= 40.0:
            assessment = "weakness"
            tag_label = "Điểm yếu đối thủ (Tỷ lệ thắng thấp)"
        elif score_pct >= 60.0:
            assessment = "stronghold"
            tag_label = "Đòn mạnh đối thủ (Tỷ lệ thắng cao)"
        else:
            assessment = "neutral"
            tag_label = "Thế trận cân bằng"

        responses_list.append({
            "first_move": selected_first_move,
            "resp_move": resp_move,
            "opening_name": data["opening_name"],
            "games_count": g_count,
            "usage_pct": usage_pct,
            "score_pct": score_pct,
            "wins": w,
            "draws": d,
            "losses": l,
            "assessment": assessment,
            "tag_label": tag_label
        })

    responses_list.sort(key=lambda x: x["games_count"], reverse=True)

    return {
        "available_first_moves": move_options,
        "selected_first_move": selected_first_move,
        "total_games_in_move": total_in_group,
        "responses": responses_list
    }


def generate_match_preparation(
    filtered_games: List[Dict[str, Any]],
    stats: Dict[str, Any],
    repertoire_data: Dict[str, Any],
    fen_map: Dict[str, Any],
    user_color: str = "white",
    lang: str = "vi",
    selected_player: str = "",
    chosen_move: str = ""
) -> Dict[str, Any]:
    """
    Tạo kế hoạch chuẩn bị trận đấu chi tiết dựa trên dữ liệu lịch sử đấu của đối thủ (Đa ngôn ngữ).
    """
    if not filtered_games:
        return {
            "target_weaknesses": [],
            "recommended_lines": [],
            "surprise_weapons": [],
            "opponent_responses": {"available_first_moves": [], "selected_first_move": "", "total_games_in_move": 0, "responses": []},
            "gameplan_checklist": [t("no_games", lang=lang)]
        }

    all_openings = repertoire_data.get("all_openings", [])
    white_rep = repertoire_data.get("white_repertoire", [])
    black_rep = repertoire_data.get("black_repertoire", [])

    # Phân tích phản ứng đối thủ theo nước đi chủ động
    opponent_responses = analyze_opponent_responses(filtered_games, user_color, chosen_move)

    # 1. Điểm yếu của đối thủ (Loss % cao hoặc Score % thấp <= 45%)
    target_weaknesses = []
    for op in all_openings:
        if op["games_count"] >= 1 and op["score_pct"] <= 45.0:
            l_pct = op.get("loss_pct", round((op.get("losses", 0) / op["games_count"]) * 100, 1) if op.get("games_count", 0) > 0 else 0.0)
            target_weaknesses.append({
                "name": op["name"],
                "games_count": op["games_count"],
                "score_pct": op["score_pct"],
                "loss_pct": l_pct,
                "reason": t("weakness_reason", lang=lang, score=op["score_pct"], loss=l_pct, count=op["games_count"])
            })
    target_weaknesses.sort(key=lambda x: x["score_pct"])

    # 2. Đề xuất phương án tác chiến theo Màu quân của Người dùng
    recommended_lines = []
    
    if user_color == "white":
        # Bạn cầm Trắng -> Đối thủ cầm Đen
        weak_black_ops = [b for b in black_rep if b["score_pct"] <= 50.0]
        if weak_black_ops:
            weak_black_ops.sort(key=lambda x: x["score_pct"])
            for b_op in weak_black_ops[:3]:
                recommended_lines.append({
                    "title": t("rec_target_line_title", lang=lang, name=b_op['name']),
                    "detail": t("rec_target_line_detail", lang=lang, score=b_op['score_pct']),
                    "priority": "High" if b_op["score_pct"] < 40.0 else "Medium"
                })
        else:
            if black_rep:
                most_played_b = max(black_rep, key=lambda x: x["games_count"])
                recommended_lines.append({
                    "title": t("rec_main_weapon_black_title", lang=lang, name=most_played_b['name']),
                    "detail": t("rec_main_weapon_black_detail", lang=lang, count=most_played_b['games_count'], score=most_played_b['score_pct']),
                    "priority": "Medium"
                })
    else:
        # Bạn cầm Đen -> Đối thủ cầm Trắng
        weak_white_ops = [w for w in white_rep if w["score_pct"] <= 50.0]
        if weak_white_ops:
            weak_white_ops.sort(key=lambda x: x["score_pct"])
            for w_op in weak_white_ops[:3]:
                recommended_lines.append({
                    "title": t("rec_white_weak_title", lang=lang, name=w_op['name']),
                    "detail": t("rec_white_weak_detail", lang=lang, score=w_op['score_pct']),
                    "priority": "High" if w_op["score_pct"] < 40.0 else "Medium"
                })
        else:
            if white_rep:
                most_played_w = max(white_rep, key=lambda x: x["games_count"])
                recommended_lines.append({
                    "title": t("rec_white_main_title", lang=lang, name=most_played_w['name']),
                    "detail": t("rec_white_main_detail", lang=lang, count=most_played_w['games_count'], score=most_played_w['score_pct']),
                    "priority": "High"
                })

    # 3. Vũ khí bất ngờ (Surprise Weapons - Các nhánh hiếm gặp mà đối thủ thua)
    surprise_weapons = []
    for fen, node in fen_map.items():
        if node.games_count >= 1 and node.games_count <= 3 and node.losses >= 1:
            win_pct = round((node.wins / node.games_count) * 100, 1)
            if win_pct < 34.0:
                surprise_weapons.append({
                    "move_san": node.move_san,
                    "fen": fen,
                    "games_count": node.games_count,
                    "losses": node.losses,
                    "note": t("surprise_note", lang=lang, losses=node.losses, count=node.games_count)
                })
                if len(surprise_weapons) >= 3:
                    break

    # 4. Actionable Checklist (Sử dụng đúng kỳ thủ đối thủ được chọn)
    target_opponent = selected_player if selected_player else "Opponent"
    checklist = [
        t("chk_side", lang=lang, color=user_color.upper(), opponent=target_opponent),
        t("chk_perf", lang=lang, score=stats.get('score_percentage', 0), w=stats.get('wins', 0), d=stats.get('draws', 0), l=stats.get('losses', 0)),
    ]

    if recommended_lines:
        checklist.append(t("chk_priority", lang=lang, title=recommended_lines[0]['title'], detail=recommended_lines[0]['detail']))
    
    if target_weaknesses:
        checklist.append(t("chk_weakness", lang=lang, name=target_weaknesses[0]['name'], score=target_weaknesses[0]['score_pct']))
    else:
        checklist.append(t("chk_weakness_none", lang=lang))

    checklist.append(t("chk_strategy", lang=lang))

    return {
        "target_weaknesses": target_weaknesses[:5],
        "recommended_lines": recommended_lines,
        "surprise_weapons": surprise_weapons,
        "opponent_responses": opponent_responses,
        "gameplan_checklist": checklist
    }


def generate_actionable_match_preparation(
    deep_profile: Dict[str, Any],
    user_color: str = "white",
    lang: str = "vi"
) -> Dict[str, Any]:
    """
    Chuyển đổi các phát hiện từ Deep Opponent Profile thành Kế hoạch Thi đấu Ngắn gọn & Có thể Hành động (Decision Support Match Prep).
    Kết hợp đa chiều: Repertoire, Structures, Phases, Dynamics, Simplification, và Playing Style Profile.
    """
    repertoire = deep_profile.get("repertoire", {})
    structures = deep_profile.get("structures", {})
    phases = deep_profile.get("phases", {})
    dynamics = deep_profile.get("dynamics", {})
    simplification = deep_profile.get("simplification", {})
    style_profile = deep_profile.get("style_profile", {})
    critical_positions = deep_profile.get("critical_positions", [])

    # A. Khai cuộc Mạnh nhất & Yếu nhất của đối thủ
    all_openings = repertoire.get("all_openings", [])
    target_rep = repertoire.get("black_repertoire" if user_color == "white" else "white_repertoire", all_openings)

    eligible_ops = [op for op in target_rep if op.get("games_count", 0) >= 1]
    strongest_op = max(eligible_ops, key=lambda x: (x["score_pct"], x["games_count"])) if eligible_ops else None
    weakest_op = min(eligible_ops, key=lambda x: (x["score_pct"], -x["games_count"])) if eligible_ops else None

    # B. Target Structure
    target_struct = structures.get("target_structure")

    # C. Vulnerability Phase
    weakest_phase = phases.get("weakest_phase")

    # D. Game Dynamics & Style Profile
    throw_rate = dynamics.get("throw_rate", 0.0)
    resilience_rate = dynamics.get("resilience_rate", 0.0)
    primary_style_key = style_profile.get("primary_key", "")
    scores = style_profile.get("scores", {})
    tactical_score = scores.get("tactical", 50.0)
    positional_score = scores.get("positional", 50.0)
    solid_score = scores.get("solid", 50.0)
    universal_score = scores.get("universal", 50.0)

    # E. Final Game Plan (PLAY, TARGET, AVOID)
    play_recs = []
    target_recs = []
    avoid_recs = []

    # --- 1. PLAY Recommendations ---
    if weakest_phase and weakest_phase.get("phase") == "endgame":
        play_recs.append(
            "Đưa trận đấu về Cờ tàn (Endgame) khi vị trí thuận lợi vì đối thủ sụt giảm độ chính xác rõ rệt."
            if lang == "vi" else
            "Simplify into technical Endgame when position is favorable due to opponent's accuracy drop."
        )
    elif weakest_phase and weakest_phase.get("phase") == "middlegame":
        play_recs.append(
            "Duy trì sức ép phức tạp trong Trung cuộc để khai thác điểm yếu xử lý trung cuộc của đối thủ."
            if lang == "vi" else
            "Maintain complex middlegame pressure to exploit opponent's middlegame inaccuracy."
        )
    else:
        play_recs.append(
            "Thi đấu chắc chắn, phát triển quân hài hòa và tuân thủ nguyên tắc vị trí."
            if lang == "vi" else
            "Play solid positional chess and focus on harmonious piece development."
        )

    # Đề xuất bổ trợ từ Style Profile
    if primary_style_key == "tactical" and tactical_score >= 65.0:
        off_res = simplification.get("queens_off", {})
        if off_res.get("score_pct", 50.0) <= 45.0:
            play_recs.append(
                "Khóa chặt cấu trúc Tốt trung tâm và chủ động đổi Hậu sớm để triệt tiêu hỏa lực tấn công của đối thủ."
                if lang == "vi" else
                "Lock central pawn structures and look for early queen trades to neutralize opponent's attacking momentum."
            )
        else:
            play_recs.append(
                "Ưu tiên các phương án làm giảm độ biến động thế cờ (Low Volatility), tránh để đối thủ mở toang trung lộ."
                if lang == "vi" else
                "Prioritize variations that minimize tactical volatility and prevent central line openings."
            )
    elif primary_style_key == "positional" and positional_score >= 65.0:
        play_recs.append(
            "Chủ động phá vỡ cấu trúc Tốt và mở cột giao tranh, không đánh thụ động để tránh bị đối thủ bóp nghẹt không gian."
            if lang == "vi" else
            "Actively challenge pawn structures and open files to avoid being slowly out-maneuvered in passive positions."
        )
    elif primary_style_key == "solid" and solid_score >= 65.0:
        play_recs.append(
            "Duy trì sức ép kiên nhẫn, không vội vàng dồn toàn lực công phá mạo hiểm dễ dính bẫy phản công."
            if lang == "vi" else
            "Maintain steady, well-coordinated pressure without overextending into counterattack traps."
        )

    if throw_rate >= 25.0:
        play_recs.append(
            f"Duy trì kiên trì khi bị lép vế vì đối thủ có tỷ lệ quăng lợi thế cao ({throw_rate}% throw rate)."
            if lang == "vi" else
            f"Stay resilient when behind; opponent shows a high advantage throw rate ({throw_rate}%)."
        )

    # --- 2. TARGET Recommendations ---
    if target_struct:
        target_recs.append(
            f"Chủ động lái trận đấu về cấu trúc {target_struct['name']} (đối thủ chỉ đạt {target_struct['score_pct']}% score)."
            if lang == "vi" else
            f"Aim for {target_struct['name']} structure (opponent scores only {target_struct['score_pct']}%)."
        )

    if weakest_op:
        target_recs.append(
            f"Khai thác hệ thống {weakest_op['name']} (đối thủ đạt {weakest_op['score_pct']}% score)."
            if lang == "vi" else
            f"Target {weakest_op['name']} (opponent scores {weakest_op['score_pct']}%)."
        )

    # --- 3. AVOID Recommendations ---
    if strongest_op and strongest_op.get("score_pct", 0) >= 55.0:
        avoid_recs.append(
            f"Tránh đi vào biến chuẩn bị mạnh nhất của đối thủ: {strongest_op['name']} ({strongest_op['score_pct']}% score) trừ khi đã chuẩn bị kỹ."
            if lang == "vi" else
            f"Avoid opponent's strongest line: {strongest_op['name']} ({strongest_op['score_pct']}% score) unless specifically prepared."
        )

    if not avoid_recs:
        avoid_recs.append(
            "Tránh các phương án chiến thuật bẫy rủi ro cao chưa chuẩn bị kỹ."
            if lang == "vi" else
            "Avoid unprepared high-risk tactical lines."
        )

    return {
        "strongest_opening": strongest_op,
        "weakest_opening": weakest_op,
        "target_structure": target_struct,
        "vulnerability_phase": weakest_phase,
        "throw_rate": throw_rate,
        "resilience_rate": resilience_rate,
        "style_profile": style_profile,
        "play_plan": play_recs,
        "target_plan": target_recs,
        "avoid_plan": avoid_recs,
        "training_positions": critical_positions[:3]
    }


