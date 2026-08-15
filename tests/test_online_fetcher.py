import pytest
from src.online_fetcher import fetch_lichess_games, fetch_chesscom_games

def test_fetch_empty_username():
    data, err = fetch_lichess_games("")
    assert data is None
    assert "không được để trống" in err

    data_c, err_c = fetch_chesscom_games("   ")
    assert data_c is None
    assert "không được để trống" in err_c

def test_fetch_nonexistent_user():
    data, err = fetch_lichess_games("this_user_definitely_does_not_exist_99999")
    assert data is None
    assert "không tồn tại" in err or "Lỗi" in err

    data_c, err_c = fetch_chesscom_games("this_user_definitely_does_not_exist_99999")
    assert data_c is None
    assert "không tồn tại" in err_c or "Lỗi" in err_c
