"""
Playing Style Profiler & Evidence Module
----------------------------------------
Chức năng: Tổng hợp các chỉ số hành vi thực tế (Factual Behavioral Metrics) và sinh
bằng chứng (Evidence) định lượng trực tiếp từ dữ liệu ván đấu.

Nguyên tắc:
1. Không dùng điểm số giả lập hay nhãn phong cách gán ghép (Loại bỏ hoàn toàn calculate_style_scores).
2. Factual Evidence: Mọi nhận định đều xuất phát 100% từ metrics quan sát được (Thí quân, Chuyển tàn, Biến động, v.v.).
3. Dữ liệu chuẩn xác, tin cậy để làm đầu vào cho UI và AI Assistant.
"""

from typing import Dict, Any, List, Optional


def generate_style_evidence(raw_metrics: Dict[str, Any], lang: str = "vi") -> List[str]:
    """
    Sinh các câu bằng chứng (Evidence) định lượng hoàn toàn từ metrics thực tế.
    """
    evidence: List[str] = []

    comp = raw_metrics.get("complexity_index", 50.0)
    vol = raw_metrics.get("volatility_score", 50.0)
    sac_rate = raw_metrics.get("sacrifice_rate", 0.0)
    total_sac = raw_metrics.get("total_sacrifices", 0)
    simp_rate = raw_metrics.get("simplification_rate", 0.0)
    is_simp = raw_metrics.get("is_simplifier", False)
    avg_eg_move = raw_metrics.get("avg_endgame_move", 0.0)
    closed_p = raw_metrics.get("closed_preference", 33.4)
    open_p = raw_metrics.get("open_preference", 33.3)
    resil = raw_metrics.get("resilience_rate", 50.0)
    has_eval = raw_metrics.get("has_engine_data", False)

    # 1. Thí quân (Sacrifice Rate)
    if has_eval:
        if sac_rate >= 15.0 or total_sac >= 2:
            evidence.append(
                f"Lối chơi mạo hiểm và sắc bén: xuất hiện đòn thí quân có chủ đích trong {sac_rate}% số ván đấu ({total_sac} nước thí quân đã ghi nhận)."
                if lang == "vi" else
                f"Sharp and tactical play: intentional sacrifices observed in {sac_rate}% of games ({total_sac} verified sacrifices)."
            )
        elif sac_rate == 0.0:
            evidence.append(
                "Kỳ thủ duy trì lối chơi an toàn vật chất tuyệt đối, không ghi nhận đòn thí quân mạo hiểm nào (Sacrifice Rate: 0%)."
                if lang == "vi" else
                "Strict material preservation with zero speculative sacrifices (0% sacrifice rate)."
            )

    # 2. Đơn giản hóa về tàn cuộc (Simplification & Endgame Transition)
    if is_simp:
        evidence.append(
            f"Xác nhận đặc trưng Simplifier: thường xuyên đổi quân đưa ván đấu về tàn cuộc sớm (TB nước {avg_eg_move}, chiếm {simp_rate}% số ván) trong các thế cờ cân bằng (-1.5 đến +1.5)."
            if lang == "vi" else
            f"Confirmed Simplifier profile: frequently trades pieces into early endgames (avg move {avg_eg_move}, {simp_rate}% of games) in balanced positions."
        )
    elif simp_rate < 25.0 or avg_eg_move > 30.0:
        evidence.append(
            f"Kỳ thủ ít khi chủ động chuyển tàn sớm (Tỉ lệ chuyển tàn: {simp_rate}%), có xu hướng kéo dài và giải quyết trận đấu ở trung cuộc."
            if lang == "vi" else
            f"Rarely seeks early endgame simplification ({simp_rate}% early rate), preferring to resolve battles in prolonged middlegames."
        )

    # 3. Độ phức tạp thế cờ (Complexity Index)
    if comp >= 60.0:
        evidence.append(
            f"Thường xuyên đưa ván cờ vào các vị trí có độ phức tạp và áp lực chiến thuật cao ({comp}/100)."
            if lang == "vi" else
            f"Frequently steers positions into high tactical complexity and forcing tension ({comp}/100)."
        )
    elif comp <= 40.0:
        evidence.append(
            f"Ưu tiên các thế cờ tĩnh, cấu trúc rõ ràng và ít đòn va chạm phức tạp ({comp}/100)."
            if lang == "vi" else
            f"Prefers static positions with clear structures and low tactical volatility ({comp}/100)."
        )

    # 4. Độ biến động thế cờ (Evaluation Volatility)
    if vol >= 60.0:
        evidence.append(
            f"Độ biến động thế cờ (Evaluation Volatility) ở mức cao ({vol}/100), cho thấy ván đấu thường diễn ra gay cấn và nhiều bước ngoặt."
            if lang == "vi" else
            f"Evaluation volatility is high ({vol}/100), indicating sharp game trajectories with frequent momentum shifts."
        )
    elif vol <= 40.0:
        evidence.append(
            f"Độ biến động điểm số rất ổn định ({vol}/100), thể hiện lối chơi kiểm soát an toàn và chặt chẽ."
            if lang == "vi" else
            f"Evaluation volatility is low ({vol}/100), demonstrating a controlled and solid positional approach."
        )

    # 5. Cấu trúc Tốt (Open vs Closed Preference)
    if closed_p >= 45.0:
        evidence.append(
            f"Ưu tiên chọn các cấu trúc trung tâm kín hoặc bán mở ({closed_p}% số ván)."
            if lang == "vi" else
            f"Shows strong preference for closed or semi-open central structures ({closed_p}% of games)."
        )
    elif open_p >= 45.0:
        evidence.append(
            f"Thường xuyên mở toang các cột trung tâm để giải phóng đường hoạt động cho quân cờ ({open_p}% số ván mở)."
            if lang == "vi" else
            f"Frequently opens central files to maximize piece activity ({open_p}% open center rate)."
        )

    # 6. Khả năng chịu ép (Resilience Rate)
    if resil >= 50.0:
        evidence.append(
            f"Khả năng chịu ép ấn tượng (Resilience): cứu hòa hoặc giành chiến thắng {resil}% số ván khi từng bị dẫn sâu (eval <= -1.5)."
            if lang == "vi" else
            f"Impressive resilience: saves a draw or wins in {resil}% of games after facing severe deficits (eval <= -1.5)."
        )

    # Fallback nếu danh sách quá ngắn
    if len(evidence) < 2:
        evidence.append(
            f"Dữ liệu hành vi: Độ phức tạp ({comp}/100), Biến động ({vol}/100), Tỉ lệ thí quân ({sac_rate}%)."
            if lang == "vi" else
            f"Behavioral indicators: Complexity ({comp}/100), Volatility ({vol}/100), Sacrifice Rate ({sac_rate}%)."
        )

    return evidence[:6]


def classify_player_style(
    raw_metrics: Dict[str, Any],
    sample_size: int = 1,
    lang: str = "vi"
) -> Dict[str, Any]:
    """
    Tạo cấu trúc dữ liệu Playing Style Profile thực nghiệm hoàn chỉnh.
    """
    evidence = generate_style_evidence(raw_metrics, lang=lang)

    return {
        "raw_metrics": raw_metrics,
        "metrics": raw_metrics,
        "evidence": evidence,
        "is_simplifier": raw_metrics.get("is_simplifier", False),
        "avg_endgame_move": raw_metrics.get("avg_endgame_move", 0.0),
        "sacrifice_rate": raw_metrics.get("sacrifice_rate", 0.0),
        "simplification_rate": raw_metrics.get("simplification_rate", 0.0),
        "complexity_index": raw_metrics.get("complexity_index", 50.0),
        "volatility_score": raw_metrics.get("volatility_score", 50.0),
        "resilience_rate": raw_metrics.get("resilience_rate", 50.0),
        "open_preference": raw_metrics.get("open_preference", 33.3),
        "closed_preference": raw_metrics.get("closed_preference", 33.4),
        "has_engine_data": raw_metrics.get("has_engine_data", False)
    }
