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

    lines = []
    lines.append(f"# CHESS OPPONENT ANALYSIS & MATCH PREPARATION REPORT")
    lines.append(f"**Target Opponent**: `{selected_player}`")
    lines.append(f"**Date Generated**: `{now_str}`")
    lines.append(f"**User Match Side**: `{user_color.upper()}`")
    lines.append("---")
    lines.append("")

    # 1. OVERALL STATISTICS
    lines.append("## 1. Overall Performance Statistics")
    lines.append(f"- **Total Games Analyzed**: {stats.get('total_games', 0)}")
    lines.append(f"- **Overall Score**: **{stats.get('score_percentage', 0)}%**")
    lines.append(f"- **Wins**: {stats.get('wins', 0)} ({stats.get('win_rate', 0)}%)")
    lines.append(f"- **Draws**: {stats.get('draws', 0)} ({stats.get('draw_rate', 0)}%)")
    lines.append(f"- **Losses**: {stats.get('losses', 0)} ({stats.get('loss_rate', 0)}%)")
    lines.append(f"- **White Side Record**: {stats.get('white_wins', 0)}W / {stats.get('white_draws', 0)}D / {stats.get('white_losses', 0)}L ({stats.get('white_score_percentage', 0)}% Score)")
    lines.append(f"- **Black Side Record**: {stats.get('black_wins', 0)}W / {stats.get('black_draws', 0)}D / {stats.get('black_losses', 0)}L ({stats.get('black_score_percentage', 0)}% Score)")
    lines.append("")

    # 2. RULE-BASED INSIGHTS
    lines.append("## 2. Automated Rule-Based Insights")
    if insights:
        for ins in insights:
            title = ins.get("title", "")
            text = ins.get("text", "")
            lines.append(f"- **{title}**: {text}")
    else:
        lines.append("- *No profile insights available.*")
    lines.append("")

    # 3. OPENING REPERTOIRE SUMMARY
    lines.append("## 3. Opening Repertoire Summary")
    
    most_played = repertoire_data.get("most_played", [])
    if most_played:
        lines.append("### Most Played Openings")
        for op in most_played[:5]:
            lines.append(f"- **{op['name']}**: {op['games_count']} games | Score: {op['score_pct']}% (W:{op['wins']} D:{op['draws']} L:{op['losses']})")
        lines.append("")

    white_rep = repertoire_data.get("white_repertoire", [])
    if white_rep:
        lines.append("### Opponent as White")
        for w in white_rep[:3]:
            lines.append(f"- **{w['name']}**: {w['games_count']} games | Score: {w['score_pct']}%")
        lines.append("")

    black_rep = repertoire_data.get("black_repertoire", [])
    if black_rep:
        lines.append("### Opponent as Black")
        for b in black_rep[:3]:
            lines.append(f"- **{b['name']}**: {b['games_count']} games | Score: {b['score_pct']}%")
        lines.append("")

    # 4. MATCH PREPARATION GAMEPLAN
    lines.append("## 4. Match Preparation & Tactical Gameplan")
    
    lines.append("### Pre-Match Checklist")
    for item in prep_data.get("gameplan_checklist", []):
        lines.append(f"- {item}")
    lines.append("")

    recs = prep_data.get("recommended_lines", [])
    if recs:
        lines.append("### Recommended Tactical Lines")
        for r in recs:
            lines.append(f"- **[{r.get('priority', 'Medium')} Priority] {r.get('title', '')}**: {r.get('detail', '')}")
        lines.append("")

    weaks = prep_data.get("target_weaknesses", [])
    if weaks:
        lines.append("### Target Opponent Weaknesses")
        for w in weaks:
            lines.append(f"- **{w.get('name', '')}**: Score {w.get('score_pct', 0)}% in {w.get('games_count', 0)} games ({w.get('reason', '')})")
        lines.append("")

    surprises = prep_data.get("surprise_weapons", [])
    if surprises:
        lines.append("### Surprise Lines / Unfamiliar Positions")
        for s in surprises:
            lines.append(f"- **Move `{s.get('move_san', '')}`**: {s.get('note', '')}")
        lines.append("")

    lines.append("---")
    lines.append("*Report generated automatically by Chess Opponent Analyzer.*")

    return "\n".join(lines)
