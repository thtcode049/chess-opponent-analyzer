"""
Report Generator Module
-----------------------
Chức năng: Tự động tổng hợp và xuất Báo cáo Phân tích Đối thủ & Kế hoạch Chuẩn bị Thi đấu
dưới định dạng Markdown (.md) hoặc Text (.txt) để lưu trữ và in ấn.
"""

from datetime import datetime
from typing import Dict, Any, List


def generate_markdown_report(
    selected_player: str,
    stats: Dict[str, Any],
    repertoire_data: Dict[str, Any],
    insights: List[Dict[str, str]],
    prep_data: Dict[str, Any],
    user_color: str = "white"
) -> str:
    """
    Sinh nội dung Báo cáo Phân tích dạng Markdown.

    Args:
        selected_player: Tên kỳ thủ đối thủ.
        stats: Thống kê tổng quan.
        repertoire_data: Dữ liệu Repertoire khai cuộc.
        insights: Danh sách các nhận định tự động (Rule-based).
        prep_data: Dữ liệu kế hoạch tác chiến.
        user_color: Màu quân của người chơi trong trận tới ('white' hoặc 'black').

    Returns:
        Chuỗi định dạng Markdown hoàn chỉnh.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    side_label = "TRẮNG" if user_color.lower() == "white" else "ĐEN"

    lines = []
    lines.append(f"# BÁO CÁO PHÂN TÍCH ĐỐI THỦ & KẾ HOẠCH TÁC CHIẾN CỜ VUA")
    lines.append(f"**Đối thủ mục tiêu**: `{selected_player}`")
    lines.append(f"**Thời gian khởi tạo**: `{now_str}`")
    lines.append(f"**Màu quân của bạn trong trận đấu**: `{side_label}`")
    lines.append("---")
    lines.append("")

    # 1. THỐNG KÊ TỔNG QUAN
    lines.append("## 1. Thống kê Hiệu suất Tổng quan")
    lines.append(f"- **Tổng số ván đã phân tích**: {stats.get('total_games', 0)}")
    lines.append(f"- **Điểm số Tổng thể**: **{stats.get('score_percentage', 0)}%**")
    lines.append(f"- **Thắng**: {stats.get('wins', 0)} ({stats.get('win_rate', 0)}%)")
    lines.append(f"- **Hòa**: {stats.get('draws', 0)} ({stats.get('draw_rate', 0)}%)")
    lines.append(f"- **Thua**: {stats.get('losses', 0)} ({stats.get('loss_rate', 0)}%)")
    lines.append(f"- **Thành tích khi Cầm Trắng**: {stats.get('white_wins', 0)}T / {stats.get('white_draws', 0)}H / {stats.get('white_losses', 0)}B ({stats.get('white_score_percentage', 0)}% Điểm số)")
    lines.append(f"- **Thành tích khi Cầm Đen**: {stats.get('black_wins', 0)}T / {stats.get('black_draws', 0)}H / {stats.get('black_losses', 0)}B ({stats.get('black_score_percentage', 0)}% Điểm số)")
    lines.append("")

    # 2. NHẬN ĐỊNH TỰ ĐỘNG
    lines.append("## 2. Nhận định Chiến thuật & Phong cách")
    if insights:
        for ins in insights:
            title = ins.get("title", "")
            text = ins.get("text", "")
            lines.append(f"- **{title}**: {text}")
    else:
        lines.append("- *Chưa có nhận định cụ thể.*")
    lines.append("")

    # 3. DANH MỤC KHAI CUỘC
    lines.append("## 3. Tóm tắt Danh mục Khai cuộc")
    
    most_played = repertoire_data.get("most_played", [])
    if most_played:
        lines.append("### Khai cuộc chơi nhiều nhất")
        for op in most_played[:5]:
            lines.append(f"- **{op['name']}**: {op['games_count']} ván | Điểm số: {op['score_pct']}% (T:{op['wins']} H:{op['draws']} B:{op['losses']})")
        lines.append("")

    white_rep = repertoire_data.get("white_repertoire", [])
    if white_rep:
        lines.append("### Đối thủ khi Cầm Trắng")
        for w in white_rep[:3]:
            lines.append(f"- **{w['name']}**: {w['games_count']} ván | Điểm số: {w['score_pct']}%")
        lines.append("")

    black_rep = repertoire_data.get("black_repertoire", [])
    if black_rep:
        lines.append("### Đối thủ khi Cầm Đen")
        for b in black_rep[:3]:
            lines.append(f"- **{b['name']}**: {b['games_count']} ván | Điểm số: {b['score_pct']}%")
        lines.append("")

    # 4. KẾ HOẠCH TÁC CHIẾN
    lines.append("## 4. Kế hoạch Tác chiến & Chuẩn bị Trận đấu")
    
    lines.append("### Checklist trước ván đấu")
    for item in prep_data.get("gameplan_checklist", []):
        lines.append(f"- {item}")
    lines.append("")

    recs = prep_data.get("recommended_lines", [])
    if recs:
        lines.append("### Biến cờ Khuyên dùng")
        for r in recs:
            lines.append(f"- **[{r.get('priority', 'Trung bình')}] {r.get('title', '')}**: {r.get('detail', '')}")
        lines.append("")

    weaks = prep_data.get("target_weaknesses", [])
    if weaks:
        lines.append("### Điểm yếu Cần Khai thác")
        for w in weaks:
            lines.append(f"- **{w.get('name', '')}**: Điểm số {w.get('score_pct', 0)}% trong {w.get('games_count', 0)} ván ({w.get('reason', '')})")
        lines.append("")

    surprises = prep_data.get("surprise_weapons", [])
    if surprises:
        lines.append("### Đòn bất ngờ / Thế cờ lạ")
        for s in surprises:
            lines.append(f"- **Nước đi `{s.get('move_san', '')}`**: {s.get('note', '')}")
        lines.append("")

    lines.append("---")
    lines.append("*Báo cáo được khởi tạo tự động bởi Chess Opponent Analyzer.*")

    return "\n".join(lines)
