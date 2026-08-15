"""
PGN Parser Module
-----------------
Chức năng: Đọc và parse các ván đấu cờ vua từ nguồn PGN (Stream/File/String).
Trích xuất thông tin người chơi, kết quả, hệ thống khai cuộc (ECO/Opening), và danh sách nước đi (SAN).
Tự động suy luận tên khai cuộc từ các nước đi nếu file PGN không có tag [Opening].
"""

import io
from pathlib import Path
from typing import List, Dict, Any, Union, Tuple
import chess.pgn

# Bảng tra cứu suy luận Khai cuộc (Opening Heuristic Lookup) dựa trên các nước đi đầu tiên
OPENING_LOOKUP: List[Tuple[Tuple[str, ...], str, str]] = [
    (("e4", "c5"), "B20", "Sicilian Defense"),
    (("e4", "e5", "Nf3", "Nc6", "Bb5"), "C60", "Ruy Lopez"),
    (("e4", "e5", "Nf3", "Nc6", "Bc4"), "C50", "Italian Game"),
    (("e4", "e5", "Nf3", "Nc6", "d4"), "C44", "Scotch Game"),
    (("e4", "e5", "Nf3", "Nc6"), "C40", "King's Pawn Game (Four Knights)"),
    (("e4", "e5", "Nf3", "Nf6"), "C42", "Petrov's Defense"),
    (("e4", "e5", "Nf3"), "C40", "King's Knight Opening"),
    (("e4", "e5", "f4"), "C23", "King's Gambit"),
    (("e4", "e5", "Nc3"), "C25", "Vienna Game"),
    (("e4", "e5"), "C20", "King's Pawn Game"),
    (("e4", "e6", "d4", "d5"), "C00", "French Defense"),
    (("e4", "e6"), "C00", "French Defense"),
    (("e4", "c6", "d4", "d5"), "B10", "Caro-Kann Defense"),
    (("e4", "c6"), "B10", "Caro-Kann Defense"),
    (("e4", "d5"), "B01", "Scandinavian Defense"),
    (("e4", "g6"), "B06", "Modern Defense"),
    (("e4", "Nf6"), "B02", "Alekhine's Defense"),
    (("e4", "d6"), "B07", "Pirc Defense"),
    (("d4", "Nf6", "c4", "e6", "Nf3"), "E10", "Queen's Indian Defense"),
    (("d4", "Nf6", "c4", "e6", "Nc3"), "E20", "Nimzo-Indian Defense"),
    (("d4", "Nf6", "c4", "g6"), "E60", "King's Indian Defense"),
    (("d4", "Nf6", "c4", "c5"), "A56", "Benoni Defense"),
    (("d4", "Nf6", "c4"), "A45", "Indian Defense"),
    (("d4", "Nf6", "Bg5"), "A45", "Trompowsky Attack"),
    (("d4", "Nf6", "Bf4"), "A45", "London System"),
    (("d4", "Nf6"), "A45", "Indian Defense"),
    (("d4", "d5", "c4", "e6"), "D30", "Queen's Gambit Declined"),
    (("d4", "d5", "c4", "c6"), "D10", "Slav Defense"),
    (("d4", "d5", "c4", "dxc4"), "D20", "Queen's Gambit Accepted"),
    (("d4", "d5", "c4"), "D06", "Queen's Gambit"),
    (("d4", "d5", "Bf4"), "D00", "London System"),
    (("d4", "d5", "Nf3"), "D02", "Queen's Pawn Game"),
    (("d4", "d5"), "D00", "Queen's Pawn Game"),
    (("d4", "f5"), "A80", "Dutch Defense"),
    (("c4", "e5"), "A20", "English Opening (Reversed Sicilian)"),
    (("c4", "c5"), "A30", "English Opening (Symmetrical)"),
    (("c4", "Nf6"), "A15", "English Opening"),
    (("c4",), "A10", "English Opening"),
    (("Nf3", "d5"), "A06", "Reti Opening"),
    (("Nf3", "Nf6"), "A04", "Zukertort Opening"),
    (("Nf3",), "A04", "Zukertort Opening"),
    (("g3",), "A00", "Hungarian Opening"),
    (("b3",), "A00", "Nimzo-Larsen Attack"),
    (("f4",), "A02", "Bird's Opening"),
    (("b4",), "A00", "Sokolsky (Polish) Opening"),
]


def infer_opening_from_moves(moves: List[str]) -> Tuple[str, str]:
    """
    Suy luận mã ECO và tên Khai cuộc dựa trên các nước đi SAN đầu tiên nếu PGN thiếu tag [Opening].
    """
    if not moves:
        return ("", "Unknown Opening")
    moves_tuple = tuple(moves)
    for prefix, eco, name in OPENING_LOOKUP:
        if moves_tuple[: len(prefix)] == prefix:
            return (eco, name)

    if len(moves) >= 2:
        return ("", f"1.{moves[0]} {moves[1]}")
    if len(moves) == 1:
        return ("", f"1.{moves[0]}")
    return ("", "Unknown Opening")


def parse_single_game(game: chess.pgn.Game) -> Dict[str, Any]:
    """
    Trích xuất các trường thông tin cơ bản từ một ván đấu chess.pgn.Game.
    """
    headers = game.headers
    board = game.board()
    moves = []

    for move in game.mainline_moves():
        moves.append(board.san(move))
        board.push(move)

    raw_eco = headers.get("ECO", "").strip()
    raw_op = headers.get("Opening", "").strip()

    # Tự động suy luận tên khai cuộc nếu tag PGN thô bị rỗng hoặc Unknown
    if not raw_op or raw_op.lower() in ["unknown opening", "unknown", ""]:
        inferred_eco, inferred_op = infer_opening_from_moves(moves)
        opening = inferred_op
        eco = raw_eco if raw_eco else inferred_eco
    else:
        opening = raw_op
        eco = raw_eco

    return {
        "event": headers.get("Event", "Unknown Event"),
        "site": headers.get("Site", "Unknown Site"),
        "date": headers.get("Date", "????.??.??"),
        "round": headers.get("Round", "?"),
        "white": headers.get("White", "Unknown White").strip(),
        "black": headers.get("Black", "Unknown Black").strip(),
        "result": headers.get("Result", "*"),
        "white_elo": _parse_elo(headers.get("WhiteElo", "0")),
        "black_elo": _parse_elo(headers.get("BlackElo", "0")),
        "eco": eco,
        "opening": opening,
        "moves": moves,
        "ply_count": len(moves),
    }


def _parse_elo(elo_str: str) -> int:
    """Chuyển đổi chuỗi Elo thành số nguyên an toàn."""
    try:
        val = int(elo_str)
        return val if val > 0 else 0
    except (ValueError, TypeError):
        return 0


def parse_pgn(
    pgn_source: Union[str, Path, io.StringIO, io.BytesIO, io.TextIOBase]
) -> List[Dict[str, Any]]:
    """
    Đọc và parse tất cả các ván đấu từ nguồn PGN (đường dẫn file, string, hoặc file-like stream).
    """
    parsed_games = []

    if isinstance(pgn_source, (str, Path)):
        file_path = Path(pgn_source)
        if not file_path.exists():
            raise FileNotFoundError(f"File PGN không tồn tại: {file_path}")
        with open(file_path, encoding="utf-8", errors="replace") as f:
            parsed_games = _read_games_from_stream(f)
    elif isinstance(pgn_source, bytes):
        text_stream = io.StringIO(pgn_source.decode("utf-8", errors="replace"))
        parsed_games = _read_games_from_stream(text_stream)
    elif isinstance(pgn_source, io.StringIO) or hasattr(pgn_source, "read"):
        if hasattr(pgn_source, "getvalue") and isinstance(pgn_source.getvalue(), bytes):
            text_stream = io.StringIO(pgn_source.getvalue().decode("utf-8", errors="replace"))
            parsed_games = _read_games_from_stream(text_stream)
        elif hasattr(pgn_source, "getvalue") and isinstance(pgn_source.getvalue(), str):
            text_stream = io.StringIO(pgn_source.getvalue())
            parsed_games = _read_games_from_stream(text_stream)
        else:
            parsed_games = _read_games_from_stream(pgn_source)
    else:
        raise ValueError("Nguồn dữ liệu PGN không hợp lệ.")

    return parsed_games


def _read_games_from_stream(stream) -> List[Dict[str, Any]]:
    """Đọc từng game từ stream, bỏ qua ván lỗi mà không làm sập ứng dụng."""
    games = []
    while True:
        try:
            game = chess.pgn.read_game(stream)
            if game is None:
                break
            parsed_game = parse_single_game(game)
            games.append(parsed_game)
        except Exception:
            continue
    return games


def extract_players(games: List[Dict[str, Any]]) -> Dict[str, int]:
    """Thống kê tần suất xuất hiện của tất cả các kỳ thủ trong PGN."""
    player_counts: Dict[str, int] = {}
    for g in games:
        w = g.get("white", "").strip()
        b = g.get("black", "").strip()
        if w and w != "Unknown White":
            player_counts[w] = player_counts.get(w, 0) + 1
        if b and b != "Unknown Black":
            player_counts[b] = player_counts.get(b, 0) + 1

    return dict(sorted(player_counts.items(), key=lambda item: item[1], reverse=True))


def detect_primary_player(games: List[Dict[str, Any]]) -> str:
    """Tự động xác định kỳ thủ chính (nhiều ván nhất)."""
    players = extract_players(games)
    if not players:
        return ""
    return next(iter(players.keys()))


def filter_games_by_player(
    games: List[Dict[str, Any]], player_name: str
) -> List[Dict[str, Any]]:
    """Lọc danh sách ván đấu của riêng kỳ thủ được chọn."""
    filtered = []
    player_name_clean = player_name.strip().lower()

    for g in games:
        w_clean = g.get("white", "").strip().lower()
        b_clean = g.get("black", "").strip().lower()

        if player_name_clean in w_clean:
            g_copy = dict(g)
            g_copy["player_color"] = "white"
            g_copy["opponent"] = g.get("black", "Unknown Black")
            filtered.append(g_copy)
        elif player_name_clean in b_clean:
            g_copy = dict(g)
            g_copy["player_color"] = "black"
            g_copy["opponent"] = g.get("white", "Unknown White")
            filtered.append(g_copy)

    return filtered
