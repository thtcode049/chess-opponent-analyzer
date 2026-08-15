from pathlib import Path
from src.pgn_parser import parse_pgn, filter_games_by_player
from src.statistics import calculate_game_stats
from src.opening_tree import build_opening_tree
from src.player_profile import analyze_opening_repertoire, generate_player_insights
from src.match_prep import generate_match_preparation
from src.report_generator import generate_markdown_report


def test_generate_markdown_report():
    sample_path = Path("data/sample.pgn")
    games = parse_pgn(sample_path)
    nep_games = filter_games_by_player(games, "Nepomniachtchi, Ian")
    
    stats = calculate_game_stats(nep_games)
    _, fen_map = build_opening_tree(nep_games)
    repertoire_data = analyze_opening_repertoire(nep_games)
    insights = generate_player_insights(nep_games, stats, repertoire_data, fen_map)
    prep_data = generate_match_preparation(nep_games, stats, repertoire_data, fen_map, user_color="white")
    
    report_md = generate_markdown_report(
        "Nepomniachtchi, Ian", stats, repertoire_data, insights, prep_data, user_color="white"
    )
    
    assert "# CHESS OPPONENT ANALYSIS & MATCH PREPARATION REPORT" in report_md
    assert "Nepomniachtchi, Ian" in report_md
    assert "## 1. Overall Performance Statistics" in report_md
    assert "## 4. Match Preparation & Tactical Gameplan" in report_md
    assert len(report_md) > 500
