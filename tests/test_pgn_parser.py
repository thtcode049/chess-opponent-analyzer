import io
from pathlib import Path
import pytest
from src.pgn_parser import (
    parse_pgn,
    _parse_elo,
    extract_players,
    detect_primary_player,
    filter_games_by_player,
)


def test_parse_elo():
    assert _parse_elo("2795") == 2795
    assert _parse_elo("?") == 0
    assert _parse_elo("") == 0
    assert _parse_elo("invalid") == 0


def test_parse_valid_pgn_file():
    sample_path = Path("data/sample.pgn")
    games = parse_pgn(sample_path)
    
    assert len(games) == 3
    
    # Kiểm tra ván 1
    g1 = games[0]
    assert g1["white"] == "Nepomniachtchi, Ian"
    assert g1["black"] == "Ding, Liren"
    assert g1["result"] == "1/2-1/2"
    assert g1["white_elo"] == 2795
    assert g1["black_elo"] == 2788
    assert g1["eco"] == "C84"
    assert g1["moves"][0] == "e4"
    assert g1["moves"][1] == "e5"


def test_extract_players():
    sample_path = Path("data/sample.pgn")
    games = parse_pgn(sample_path)
    players_dict = extract_players(games)
    
    # Nepomniachtchi và Ding Liren đều tham gia 2 trận trong sample.pgn
    assert "Nepomniachtchi, Ian" in players_dict
    assert "Ding, Liren" in players_dict
    assert players_dict["Nepomniachtchi, Ian"] == 2
    assert players_dict["Ding, Liren"] == 2
    assert players_dict["PlayerA"] == 1


def test_detect_primary_player():
    sample_path = Path("data/sample.pgn")
    games = parse_pgn(sample_path)
    primary = detect_primary_player(games)
    
    # Kỳ thủ xuất hiện nhiều nhất phải nằm trong nhóm top 2 (Nepomniachtchi hoặc Ding Liren)
    assert primary in ["Nepomniachtchi, Ian", "Ding, Liren"]


def test_filter_games_by_player():
    sample_path = Path("data/sample.pgn")
    games = parse_pgn(sample_path)
    
    # Lọc cho Nepomniachtchi, Ian
    nep_games = filter_games_by_player(games, "Nepomniachtchi, Ian")
    assert len(nep_games) == 2
    
    # Ván 1: Nepomniachtchi cầm White
    assert nep_games[0]["player_color"] == "white"
    assert nep_games[0]["opponent"] == "Ding, Liren"

    # Ván 2: Nepomniachtchi cầm Black
    assert nep_games[1]["player_color"] == "black"
    assert nep_games[1]["opponent"] == "Ding, Liren"


def test_corrupted_pgn_handling():
    corrupted_pgn = """
[Event "Valid Game 1"]
[White "W1"]
[Black "B1"]
[Result "1-0"]

1. e4 e5 1-0

INVALID PGN HEADER WITHOUT BRACKETS
random text 123456 !!!

[Event "Valid Game 2"]
[White "W2"]
[Black "B2"]
[Result "0-1"]

1. d4 d5 0-1
"""
    stream = io.StringIO(corrupted_pgn)
    games = parse_pgn(stream)
    
    assert len(games) >= 1
    assert any(g["white"] == "W1" for g in games)


def test_non_existent_file():
    with pytest.raises(FileNotFoundError):
        parse_pgn("non_existent_file_123.pgn")
