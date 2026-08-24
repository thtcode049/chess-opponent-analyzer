"""
Sample Size & Confidence Rating Module
---------------------------------------
Chức năng: Tính toán mức độ tin cậy (Confidence Level) của các kết luận phân tích dựa trên kích thước mẫu (Sample Size).
"""

from typing import Dict, Any


def get_confidence_level(sample_size: int) -> str:
    if sample_size >= 10:
        return "HIGH"
    elif sample_size >= 5:
        return "MEDIUM"
    else:
        return "LOW"


def format_confidence_label(sample_size: int, lang: str = "vi") -> Dict[str, Any]:
    level = get_confidence_level(sample_size)
    if level == "HIGH":
        label = "Độ tin cậy Cao"
        color = "#22C55E"
    elif level == "MEDIUM":
        label = "Độ tin cậy Trung bình"
        color = "#EAB308"
    else:
        label = "Độ tin cậy Thấp (Cần thêm dữ liệu)"
        color = "#94A3B8"

    return {
        "level": level,
        "sample_size": sample_size,
        "label": label,
        "color": color,
    }
