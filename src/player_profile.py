"""
Player Profile & Opening Repertoire Module
------------------------------------------
Chức năng: Phân tích danh mục khai cuộc (Opening Repertoire) và sinh các nhận định
tự động (Rule-Based Insights) hỗ trợ người chơi nhận diện phong cách của đối thủ.
"""

from typing import List, Dict, Any, Optional
from src.i18n import t
from src.ui_components import get_icon_svg


def _get_opening_label(game: Dict[str, Any]) -> str:
    opening = game.get("opening", "").strip()
    eco = game.get("eco", "").strip()
    moves = game.get("moves", [])

    if opening and eco:
        return f"{eco} - {opening}"
    if eco:
        return f"ECO {eco}"
    if opening:
        return opening
    if len(moves) >= 2:
        return f"1.{moves[0]} {moves[1]}"
    if len(moves) == 1:
        return f"1.{moves[0]}"
    return "Unknown Opening"


def analyze_opening_repertoire(
    filtered_games: List[Dict[str, Any]],
    min_sample: int = 1
) -> Dict[str, Any]:
    """
    Phân tích Repertoire khai cuộc của đối thủ, chia theo tổng thể, màu Trắng và màu Đen.
    """
    openings_map: Dict[str, Dict[str, int]] = {}
    white_map: Dict[str, Dict[str, int]] = {}
    black_map: Dict[str, Dict[str, int]] = {}

    total_games = len(filtered_games)

    for game in filtered_games:
        opening_name = game.get("opening", "Unknown Opening").strip()
        if not opening_name:
            opening_name = "Unknown Opening"

        player_color = game.get("player_color", "white")
        result = game.get("result", "*")

        is_win = False
        is_draw = False
        is_loss = False

        if result == "1/2-1/2":
            is_draw = True
        elif (player_color == "white" and result == "1-0") or (player_color == "black" and result == "0-1"):
            is_win = True
        elif (player_color == "white" and result == "0-1") or (player_color == "black" and result == "1-0"):
            is_loss = True

        def _update_stats(target_dict: dict, op_name: str):
            if op_name not in target_dict:
                target_dict[op_name] = {"games": 0, "wins": 0, "draws": 0, "losses": 0}
            target_dict[op_name]["games"] += 1
            if is_win:
                target_dict[op_name]["wins"] += 1
            elif is_draw:
                target_dict[op_name]["draws"] += 1
            elif is_loss:
                target_dict[op_name]["losses"] += 1

        _update_stats(openings_map, opening_name)
        if player_color == "white":
            _update_stats(white_map, opening_name)
        else:
            _update_stats(black_map, opening_name)

    def _finalize_list(target_dict: dict, denominator: int) -> List[Dict[str, Any]]:
        result_list = []
        for name, data in target_dict.items():
            g_count = data["games"]
            w = data["wins"]
            d = data["draws"]
            l = data["losses"]

            usage_pct = round((g_count / denominator) * 100, 1) if denominator > 0 else 0.0
            score_pct = round(((w + 0.5 * d) / g_count) * 100, 1) if g_count > 0 else 0.0
            win_pct = round((w / g_count) * 100, 1) if g_count > 0 else 0.0
            draw_pct = round((d / g_count) * 100, 1) if g_count > 0 else 0.0
            loss_pct = round((l / g_count) * 100, 1) if g_count > 0 else 0.0

            result_list.append({
                "name": name,
                "games_count": g_count,
                "usage_pct": usage_pct,
                "score_pct": score_pct,
                "win_pct": win_pct,
                "draw_pct": draw_pct,
                "loss_pct": loss_pct,
                "wins": w,
                "draws": d,
                "losses": l,
            })
        return result_list

    all_openings = _finalize_list(openings_map, total_games)
    white_repertoire = _finalize_list(white_map, sum(1 for g in filtered_games if g.get("player_color") == "white"))
    black_repertoire = _finalize_list(black_map, sum(1 for g in filtered_games if g.get("player_color") == "black"))

    most_played = sorted(all_openings, key=lambda x: x["games_count"], reverse=True)
    eligible = [op for op in all_openings if op["games_count"] >= min_sample]
    best_scoring = sorted(eligible, key=lambda x: (x["score_pct"], x["games_count"]), reverse=True)
    worst_scoring = sorted(eligible, key=lambda x: (x["score_pct"], -x["games_count"]))

    return {
        "all_openings": most_played,
        "most_played": most_played[:5],
        "best_scoring": best_scoring[:5],
        "worst_scoring": worst_scoring[:5],
        "white_repertoire": sorted(white_repertoire, key=lambda x: x["games_count"], reverse=True),
        "black_repertoire": sorted(black_repertoire, key=lambda x: x["games_count"], reverse=True),
    }


def generate_player_insights(
    filtered_games: List[Dict[str, Any]],
    stats: Dict[str, Any],
    repertoire_data: Dict[str, Any],
    tree_data: Dict[str, Any],
    lang: str = "vi"
) -> List[Dict[str, str]]:
    """
    Sinh danh sách các Insight (Rule-based) tự động đa ngôn ngữ.
    """
    insights = []
    total_games = len(filtered_games)

    if total_games == 0:
        return [{"type": "info", "icon": "💡", "title": "No Data", "text": "No game data available for analysis."}]

    # 1. Preferred First Move as White
    white_games = [g for g in filtered_games if g.get("player_color") == "white"]
    if white_games:
        first_moves_w = {}
        for g in white_games:
            m = g.get("moves", [])
            if m:
                first_moves_w[m[0]] = first_moves_w.get(m[0], 0) + 1
        if first_moves_w:
            top_w_move = max(first_moves_w.items(), key=lambda x: x[1])
            pct_w = round((top_w_move[1] / len(white_games)) * 100, 1)
            insights.append({
                "type": "opening",
                "icon": "♟️",
                "title": t("ins_white_pref_title", lang=lang),
                "text": t("ins_white_pref_text", lang=lang, move=top_w_move[0], pct=pct_w)
            })

    # 2. Preferred Response to 1.e4 as Black
    black_games = [g for g in filtered_games if g.get("player_color") == "black"]
    if black_games:
        e4_responses = {}
        for g in black_games:
            m = g.get("moves", [])
            if len(m) >= 2 and m[0] == "e4":
                e4_responses[m[1]] = e4_responses.get(m[1], 0) + 1
        if e4_responses:
            top_e4_resp = max(e4_responses.items(), key=lambda x: x[1])
            pct_resp = round((top_e4_resp[1] / sum(e4_responses.values())) * 100, 1)
            insights.append({
                "type": "opening",
                "icon": "♟️",
                "title": t("ins_black_resp_title", lang=lang),
                "text": t("ins_black_resp_text", lang=lang, move=top_e4_resp[0], pct=pct_resp)
            })

    # 3. Color Performance Bias
    w_score = stats.get("white_score_percentage", 0.0)
    b_score = stats.get("black_score_percentage", 0.0)
    if stats.get("white_games", 0) >= 1 and stats.get("black_games", 0) >= 1:
        if w_score - b_score >= 10.0:
            insights.append({
                "type": "stat",
                "icon": "📊",
                "title": t("ins_color_bias_title", lang=lang),
                "text": t("ins_color_bias_white", lang=lang, w_score=w_score, b_score=b_score)
            })
        elif b_score - w_score >= 10.0:
            insights.append({
                "type": "stat",
                "icon": "📊",
                "title": t("ins_color_bias_title", lang=lang),
                "text": t("ins_color_bias_black", lang=lang, w_score=w_score, b_score=b_score)
            })

    # 4. Favorite Opening System
    most_played = repertoire_data.get("most_played", [])
    if most_played:
        fav = most_played[0]
        insights.append({
            "type": "repertoire",
            "icon": "🌿",
            "title": t("ins_fav_opening_title", lang=lang),
            "text": t("ins_fav_opening_text", lang=lang, name=fav['name'], count=fav['games_count'], score=fav['score_pct'])
        })

    # 5. Best Scoring Weapon
    best_scoring = repertoire_data.get("best_scoring", [])
    if best_scoring:
        best = best_scoring[0]
        if best["games_count"] >= 1:
            insights.append({
                "type": "repertoire",
                "icon": "⚔️",
                "title": t("ins_best_weapon_title", lang=lang),
                "text": t("ins_best_weapon_text", lang=lang, name=best['name'], count=best['games_count'], score=best['score_pct'])
            })

    return insights


def generate_deep_opponent_profile(
    filtered_games: List[Dict[str, Any]],
    stats: Dict[str, Any],
    move_evaluations: Optional[List[Dict[str, Any]]] = None,
    lang: str = "vi"
) -> Dict[str, Any]:
    """
    Tạo cấu trúc dữ liệu Hồ sơ Phân tích Sâu của Đối thủ (Deep Opponent Profile).
    Tích hợp tất cả các module phân tích chuyên sâu: Repertoire, Structures, Phases, Dynamics, Simplification, Habits, và Critical Positions.
    """
    from src.analysis.pawn_structure import analyze_structural_performance
    from src.analysis.phase_analysis import analyze_phase_performance
    from src.analysis.game_dynamics import analyze_game_dynamics
    from src.analysis.simplification import analyze_simplification_performance
    from src.analysis.habit_analysis import analyze_middlegame_habits
    from src.analysis.critical_positions import find_critical_positions

    repertoire_data = analyze_opening_repertoire(filtered_games)
    structures_data = analyze_structural_performance(filtered_games, move_evaluations=move_evaluations, lang=lang)
    phases_data = analyze_phase_performance(filtered_games, move_evaluations=move_evaluations, lang=lang)
    dynamics_data = analyze_game_dynamics(filtered_games, move_evaluations=move_evaluations, lang=lang)
    simplification_data = analyze_simplification_performance(filtered_games, move_evaluations=move_evaluations, lang=lang)
    habits_data = analyze_middlegame_habits(filtered_games, lang=lang)
    critical_positions = find_critical_positions(move_evaluations, max_positions=5)

    rule_insights = generate_player_insights(filtered_games, stats, repertoire_data, {}, lang=lang)

    return {
        "repertoire": repertoire_data,
        "structures": structures_data,
        "phases": phases_data,
        "dynamics": dynamics_data,
        "simplification": simplification_data,
        "habits": habits_data,
        "critical_positions": critical_positions,
        "rule_insights": rule_insights,
        "has_engine_data": bool(move_evaluations)
    }

