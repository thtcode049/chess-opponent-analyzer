"""
Online Player Games Fetcher (Lichess & Chess.com)
--------------------------------------------------
Chức năng: Tải lịch sử ván đấu trực tiếp từ tài khoản Lichess hoặc Chess.com API
tương tự như openingtree.com.
"""

import urllib.request
import urllib.parse
import json
from typing import Tuple, Optional


def fetch_lichess_games(username: str, max_games: int = 100) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Tải PGN ván đấu từ Lichess API.
    Endpoint: https://lichess.org/api/games/user/{username}
    """
    clean_user = username.strip()
    if not clean_user:
        return None, "Tên tài khoản Lichess không được để trống."

    url = f"https://lichess.org/api/games/user/{urllib.parse.quote(clean_user)}?max={max_games}&opening=true"
    
    headers = {
        "Accept": "application/x-chess-pgn",
        "User-Agent": "ChessOpponentAnalyzer/1.0"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                pgn_text = resp.read()
                if not pgn_text or len(pgn_text.strip()) == 0:
                    return None, f"Không tìm thấy ván đấu nào cho tài khoản Lichess '{clean_user}'."
                return pgn_text, None
            else:
                return None, f"Lichess API trả về mã lỗi HTTP {resp.status}."
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, f"Tài khoản Lichess '{clean_user}' không tồn tại."
        return None, f"Lỗi Lichess API (HTTP {e.code}): {e.reason}"
    except Exception as e:
        return None, f"Không thể kết nối tới Lichess: {e}"


def fetch_chesscom_games(username: str, max_games: int = 100) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Tải PGN ván đấu từ Chess.com API.
    1. Lấy danh sách Monthly Archives: https://api.chess.com/pub/player/{username}/games/archives
    2. Tải PGN từ các lưu trữ gần nhất.
    """
    clean_user = username.strip().lower()
    if not clean_user:
        return None, "Tên tài khoản Chess.com không được để trống."

    archives_url = f"https://api.chess.com/pub/player/{urllib.parse.quote(clean_user)}/games/archives"
    headers = {
        "User-Agent": "ChessOpponentAnalyzer/1.0 (contact: admin@example.com)"
    }

    try:
        req = urllib.request.Request(archives_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return None, f"Chess.com API trả về mã lỗi HTTP {resp.status}."
            data = json.loads(resp.read().decode('utf-8'))
            archives = data.get("archives", [])

        if not archives:
            return None, f"Không tìm thấy ván đấu lưu trữ nào cho tài khoản Chess.com '{clean_user}'."

        # Duyệt từ tháng gần nhất trở về trước để thu thập đủ max_games
        pgn_list = []
        games_collected = 0

        for archive_url in reversed(archives):
            if games_collected >= max_games:
                break
            
            archive_req = urllib.request.Request(archive_url, headers=headers)
            with urllib.request.urlopen(archive_req, timeout=10) as a_resp:
                if a_resp.status == 200:
                    month_data = json.loads(a_resp.read().decode('utf-8'))
                    month_games = month_data.get("games", [])
                    for g in reversed(month_games):
                        if "pgn" in g:
                            pgn_list.append(g["pgn"])
                            games_collected += 1
                            if games_collected >= max_games:
                                break

        if not pgn_list:
            return None, f"Không tìm thấy dữ liệu PGN hợp lệ cho '{clean_user}' trên Chess.com."

        combined_pgn = "\n\n".join(pgn_list).encode('utf-8')
        return combined_pgn, None

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, f"Tài khoản Chess.com '{clean_user}' không tồn tại."
        return None, f"Lỗi Chess.com API (HTTP {e.code}): {e.reason}"
    except Exception as e:
        return None, f"Không thể kết nối tới Chess.com: {e}"
