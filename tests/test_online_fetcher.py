import pytest
from src.online_fetcher import (
    fetch_lichess_games,
    fetch_chesscom_games,
    _normalize_lichess_perf_types,
    _normalize_chesscom_time_classes,
)

def test_fetch_empty_username():
    data, err = fetch_lichess_games("")
    assert data is None
    assert "không được để trống" in err

    data_c, err_c = fetch_chesscom_games("   ")
    assert data_c is None
    assert "không được để trống" in err_c

def test_fetch_nonexistent_user():
    data, err = fetch_lichess_games("this_user_definitely_does_not_exist_99999", perf_types=["Rapid"])
    assert data is None
    assert "không tồn tại" in err or "Lỗi" in err

    data_c, err_c = fetch_chesscom_games("this_user_definitely_does_not_exist_99999", perf_types=["Blitz", "Rapid"])
    assert data_c is None
    assert "không tồn tại" in err_c or "Lỗi" in err_c

def test_normalize_lichess_perf_types():
    assert _normalize_lichess_perf_types(None) is None
    assert _normalize_lichess_perf_types([]) is None
    res = _normalize_lichess_perf_types(["Rapid", "Blitz", "Daily / Correspondence"])
    assert "rapid" in res
    assert "blitz" in res
    assert "correspondence" in res

def test_normalize_chesscom_time_classes():
    assert _normalize_chesscom_time_classes(None) is None
    assert _normalize_chesscom_time_classes([]) is None
    res = _normalize_chesscom_time_classes(["Rapid", "Bullet"])
    assert res == {"rapid", "bullet"}
    res_classical = _normalize_chesscom_time_classes(["Classical"])
    assert "rapid" in res_classical

