"""
Playing Style Classifier & Profiler Module
------------------------------------------
Chức năng: Nhận 9 raw metrics đã chuẩn hóa và tính 4 điểm phong cách độc lập (0-100),
xác định Primary/Secondary Style, Confidence, và sinh bằng chứng (Evidence) định lượng.

Nguyên tắc:
1. Không hard-code nhãn duy nhất: Tính 4 điểm số độc lập.
2. Separation of Concerns: Không tạo Game Plan hay Recommendation ở module này.
3. Factual Evidence: Mọi nhận định đều xuất phát từ metrics quan sát được.
"""

from typing import Dict, Any, List, Optional
from src.i18n import t


STYLE_DEFINITIONS = {
    "tactical": {
        "key": "tactical",
        "name_vi": "Tấn công / Chiến thuật",
        "name_en": "Tactical / Aggressive",
        "icon": "⚔️",
        "archetype": "Garry Kasparov, Mikhail Tal"
    },
    "positional": {
        "key": "positional",
        "name_vi": "Thế trận / Bóp nghẹt",
        "name_en": "Positional / Prophylactic",
        "icon": "🛡️",
        "archetype": "Anatoly Karpov, Tigran Petrosian"
    },
    "universal": {
        "key": "universal",
        "name_vi": "Toàn diện / Kỹ thuật",
        "name_en": "Universal / Dynamic",
        "icon": "⚖️",
        "archetype": "Magnus Carlsen, Bobby Fischer"
    },
    "solid": {
        "key": "solid",
        "name_vi": "Phòng thủ / Phản công",
        "name_en": "Solid / Counter-Puncher",
        "icon": "🏰",
        "archetype": "Hikaru Nakamura, Sergey Karjakin"
    }
}


def calculate_style_scores(raw_metrics: Dict[str, Any]) -> Dict[str, float]:
    """
    Tính 4 điểm số phong cách độc lập từ 0 - 100.
    """
    complexity = raw_metrics.get("complexity_index", 50.0)
    volatility = raw_metrics.get("volatility_score", 50.0)
    queen_retention = raw_metrics.get("queen_retention_25", 50.0)
    simplification_rate = raw_metrics.get("simplification_rate", 40.0)
    open_pref = raw_metrics.get("open_preference", 33.3)
    closed_pref = raw_metrics.get("closed_preference", 33.4)
    prophylaxis = raw_metrics.get("prophylaxis_rate", 30.0)
    resilience = raw_metrics.get("resilience_rate", 50.0)
    counterattack = raw_metrics.get("counterattack_conversion_rate")
    phase_consistency = raw_metrics.get("phase_consistency_score", 50.0)

    low_volatility = max(0.0, min(100.0, 100.0 - volatility))
    low_prophylaxis = max(0.0, min(100.0, 100.0 - prophylaxis))
    selective_simplification = max(0.0, min(100.0, 100.0 - simplification_rate))
    structural_balance = max(0.0, min(100.0, 100.0 - abs(open_pref - closed_pref)))

    # 1. TACTICAL SCORE (0-100)
    # 30% Complexity + 25% Volatility + 15% Queen Retention + 15% Open Pref + 15% Low Prophylaxis
    tactical = (
        0.30 * complexity +
        0.25 * volatility +
        0.15 * queen_retention +
        0.15 * open_pref +
        0.15 * low_prophylaxis
    )

    # 2. POSITIONAL SCORE (0-100)
    # 30% Closed Pref + 25% Low Volatility + 20% Prophylaxis + 15% Stability (Low Volatility) + 10% Selective Simp
    positional = (
        0.30 * closed_pref +
        0.25 * low_volatility +
        0.20 * prophylaxis +
        0.15 * low_volatility +
        0.10 * selective_simplification
    )

    # 3. UNIVERSAL SCORE (0-100)
    # 40% Phase Consistency + 25% Color Consistency + 20% Structural Balance + 15% Consistent Conversion
    universal = (
        0.40 * phase_consistency +
        0.25 * phase_consistency +
        0.20 * structural_balance +
        0.15 * phase_consistency
    )

    # 4. SOLID SCORE (0-100)
    # Nếu có Counterattack Conversion: 30% Resilience + 25% Counterattack + 20% Low Volatility + 15% Closed Pref + 10% Simplification
    # Nếu không có Counterattack: Tái phân bổ trọng số (45% Resilience + 30% Low Volatility + 15% Closed Pref + 10% Simplification)
    if counterattack is not None:
        solid = (
            0.30 * resilience +
            0.25 * counterattack +
            0.20 * low_volatility +
            0.15 * closed_pref +
            0.10 * simplification_rate
        )
    else:
        solid = (
            0.45 * resilience +
            0.30 * low_volatility +
            0.15 * closed_pref +
            0.10 * simplification_rate
        )

    return {
        "tactical": round(max(0.0, min(100.0, tactical)), 1),
        "positional": round(max(0.0, min(100.0, positional)), 1),
        "universal": round(max(0.0, min(100.0, universal)), 1),
        "solid": round(max(0.0, min(100.0, solid)), 1)
    }


def determine_primary_and_secondary_style(
    scores: Dict[str, float],
    sample_size: int = 1,
    lang: str = "vi"
) -> Dict[str, Any]:
    """
    Xếp hạng style và tính toán mức độ tin cậy (Confidence).
    """
    sorted_styles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_key, primary_score = sorted_styles[0]
    secondary_key, secondary_score = sorted_styles[1]

    score_separation = round(primary_score - secondary_score, 1)

    # Tính toán mức độ tin cậy
    if sample_size >= 10 and score_separation >= 8.0:
        conf_level = "HIGH"
        conf_badge = t("conf_high", lang=lang) if lang == "vi" else "High Confidence"
        conf_color = "#22C55E"
    elif sample_size >= 5 and score_separation >= 4.0:
        conf_level = "MEDIUM"
        conf_badge = t("conf_med", lang=lang) if lang == "vi" else "Medium Confidence"
        conf_color = "#EAB308"
    else:
        conf_level = "LOW"
        conf_badge = t("conf_low", lang=lang) if lang == "vi" else "Low Confidence"
        conf_color = "#94A3B8"

    def _get_label(key: str) -> str:
        d = STYLE_DEFINITIONS.get(key, {})
        return d.get(f"name_{lang}", key.capitalize())

    def _get_icon(key: str) -> str:
        return STYLE_DEFINITIONS.get(key, {}).get("icon", "♟️")

    return {
        "primary_key": primary_key,
        "primary_name": _get_label(primary_key),
        "primary_icon": _get_icon(primary_key),
        "primary_score": primary_score,
        "secondary_key": secondary_key,
        "secondary_name": _get_label(secondary_key),
        "secondary_icon": _get_icon(secondary_key),
        "secondary_score": secondary_score,
        "score_separation": score_separation,
        "confidence_level": conf_level,
        "confidence_badge": conf_badge,
        "confidence_color": conf_color,
        "archetype": STYLE_DEFINITIONS.get(primary_key, {}).get("archetype", "")
    }


def generate_style_evidence(raw_metrics: Dict[str, Any], lang: str = "vi") -> List[str]:
    """
    Sinh 3 đến 5 câu bằng chứng (Evidence) định lượng hoàn toàn từ metrics thực tế.
    """
    evidence: List[str] = []

    comp = raw_metrics.get("complexity_index", 50.0)
    vol = raw_metrics.get("volatility_score", 50.0)
    q_ret = raw_metrics.get("queen_retention_25", 50.0)
    closed_p = raw_metrics.get("closed_preference", 33.4)
    open_p = raw_metrics.get("open_preference", 33.3)
    resil = raw_metrics.get("resilience_rate", 50.0)
    phase_c = raw_metrics.get("phase_consistency_score", 50.0)
    simp_r = raw_metrics.get("simplification_rate", 40.0)

    # 1. Complexity
    if comp >= 62.0:
        evidence.append(
            f"Kỳ thủ thường xuyên đưa ván cờ vào các vị trí có độ phức tạp và áp lực chiến thuật cao ({comp}/100)."
            if lang == "vi" else
            f"Frequently steers positions into high tactical complexity and forcing tension ({comp}/100)."
        )
    elif comp <= 38.0:
        evidence.append(
            f"Ưu tiên các thế cờ tĩnh, cấu trúc rõ ràng và ít đòn va chạm phức tạp ({comp}/100)."
            if lang == "vi" else
            f"Prefers static positions with clear structures and low tactical volatility ({comp}/100)."
        )

    # 2. Volatility
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

    # 3. Queen Retention & Simplification
    if q_ret >= 60.0:
        evidence.append(
            f"Duy trì Hậu trên bàn cờ qua nước 25 trong {q_ret}% số ván để duy trì hỏa lực công thủ."
            if lang == "vi" else
            f"Retains queens beyond move 25 in {q_ret}% of games to maintain tactical firepower."
        )
    elif simp_r >= 55.0:
        evidence.append(
            f"Có xu hướng chủ động đổi quân và đưa thế cờ về đơn giản hóa ({simp_r}% ván đổi quân nhanh)."
            if lang == "vi" else
            f"Shows a distinct tendency to trade pieces and simplify positions ({simp_r}% early simplification rate)."
        )

    # 4. Open vs Closed Preference
    if closed_p >= 48.0:
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

    # 5. Resilience
    if resil >= 55.0:
        evidence.append(
            f"Khả năng chịu ép ấn tượng (Resilience): cứu hòa hoặc giành chiến thắng {resil}% số ván khi từng bị dẫn sâu."
            if lang == "vi" else
            f"Impressive resilience: saves a draw or wins in {resil}% of games after facing severe deficits."
        )

    # 6. Phase Consistency
    if phase_c >= 65.0:
        evidence.append(
            f"Độ chính xác (ACPL) đồng đều qua cả 3 giai đoạn Khai – Trung – Tàn ({phase_c}/100)."
            if lang == "vi" else
            f"High phase consistency: uniform accuracy and ACPL across all three game phases ({phase_c}/100)."
        )

    # Fallback nếu danh sách quá ngắn
    if len(evidence) < 3:
        evidence.append(
            f"Phong cách thi đấu thể hiện sự phân bổ: Tấn công ({raw_metrics.get('complexity_index', 50)}), Phòng thủ ({raw_metrics.get('resilience_rate', 50)})."
            if lang == "vi" else
            f"Playstyle profile exhibits balanced behavioral indicators across tactical and positional dimensions."
        )

    return evidence[:5]


def classify_player_style(
    raw_metrics: Dict[str, Any],
    sample_size: int = 1,
    lang: str = "vi"
) -> Dict[str, Any]:
    """
    Tạo cấu trúc dữ liệu Playing Style Profile hoàn chỉnh.
    """
    scores = calculate_style_scores(raw_metrics)
    ranking = determine_primary_and_secondary_style(scores, sample_size=sample_size, lang=lang)
    evidence = generate_style_evidence(raw_metrics, lang=lang)

    return {
        "raw_metrics": raw_metrics,
        "scores": scores,
        "primary_style": ranking["primary_name"],
        "primary_key": ranking["primary_key"],
        "primary_icon": ranking["primary_icon"],
        "primary_score": ranking["primary_score"],
        "secondary_style": ranking["secondary_name"],
        "secondary_key": ranking["secondary_key"],
        "secondary_icon": ranking["secondary_icon"],
        "secondary_score": ranking["secondary_score"],
        "score_separation": ranking["score_separation"],
        "confidence": ranking["confidence_level"],
        "confidence_badge": ranking["confidence_badge"],
        "confidence_color": ranking["confidence_color"],
        "archetype": ranking["archetype"],
        "evidence": evidence
    }
