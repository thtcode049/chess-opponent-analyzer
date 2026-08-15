"""
Opening Tree Module
-------------------
Chức năng: Xây dựng cấu trúc cây khai cuộc Node-based Trie Structure từ các ván đấu PGN.
Mỗi nút (TreeNode) biểu diễn một trạng thái cờ (FEN) và danh sách các nhánh con (children).
"""

from typing import List, Dict, Any, Tuple
import chess


class TreeNode:
    """Nút của Cây Khai Cuộc (Opening Tree Node)."""

    def __init__(self, fen: str, move_san: str = "", move_uci: str = ""):
        self.fen = fen
        self.move_san = move_san
        self.move_uci = move_uci
        self.games_count = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.children: Dict[str, "TreeNode"] = {}  # Move_SAN -> TreeNode child
        self.games: List[Dict[str, Any]] = []


def build_opening_tree(
    filtered_games: List[Dict[str, Any]]
) -> Tuple[TreeNode, Dict[str, TreeNode]]:
    """
    Xây dựng cây Opening Tree và HashMap FEN từ danh sách các ván đấu của kỳ thủ.

    Returns:
        Tuple[TreeNode, Dict[str, TreeNode]]: Nút gốc (Starting Position) và fen_map tra cứu O(1).
    """
    root_fen = chess.Board().fen()
    root = TreeNode(root_fen)
    fen_map: Dict[str, TreeNode] = {root_fen: root}

    for game in filtered_games:
        player_color = game.get("player_color", "white")
        result = game.get("result", "*")
        moves = game.get("moves", [])

        # Xác định kết quả
        is_win = False
        is_draw = False
        is_loss = False

        if result == "1/2-1/2":
            is_draw = True
        elif (player_color == "white" and result == "1-0") or (player_color == "black" and result == "0-1"):
            is_win = True
        elif (player_color == "white" and result == "0-1") or (player_color == "black" and result == "1-0"):
            is_loss = True

        board = chess.Board()
        current_node = root

        # Cập nhật nút gốc
        current_node.games_count += 1
        current_node.games.append(game)
        if is_win:
            current_node.wins += 1
        elif is_draw:
            current_node.draws += 1
        elif is_loss:
            current_node.losses += 1

        for san_move in moves:
            try:
                move_obj = board.parse_san(san_move)
                uci_move = move_obj.uci()
                board.push(move_obj)
                next_fen = board.fen()
            except ValueError:
                # Nước đi SAN không hợp lệ
                break

            # Kiểm tra hoặc tạo nút con
            if san_move not in current_node.children:
                child_node = TreeNode(next_fen, move_san=san_move, move_uci=uci_move)
                current_node.children[san_move] = child_node
                fen_map[next_fen] = child_node
            else:
                child_node = current_node.children[san_move]
                # Đảm bảo fen_map cập nhật nút mới nhất
                fen_map[next_fen] = child_node

            child_node.games_count += 1
            child_node.games.append(game)
            if is_win:
                child_node.wins += 1
            elif is_draw:
                child_node.draws += 1
            elif is_loss:
                child_node.losses += 1

            current_node = child_node

    return root, fen_map


def get_position_details(
    fen_map: Dict[str, TreeNode], fen: str
) -> Dict[str, Any]:
    """
    Tra cứu chi tiết nút cây theo FEN vị trí bàn cờ.

    Returns:
        Dict chứa thống kê số ván, winrate, và danh sách continuations tiếp theo.
    """
    if fen not in fen_map:
        return {
            "fen": fen,
            "in_pgn": False,
            "total_games": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "score_pct": 0.0,
            "continuations": [],
        }

    node = fen_map[fen]
    total_at_node = node.games_count

    continuations_list = []
    for san_move, child in node.children.items():
        g_count = child.games_count
        w = child.wins
        d = child.draws
        l = child.losses

        usage_pct = round((g_count / total_at_node) * 100, 1) if total_at_node > 0 else 0.0
        score_pct = round(((w + 0.5 * d) / g_count) * 100, 1) if g_count > 0 else 0.0
        win_pct = round((w / g_count) * 100, 1) if g_count > 0 else 0.0
        draw_pct = round((d / g_count) * 100, 1) if g_count > 0 else 0.0
        loss_pct = round((l / g_count) * 100, 1) if g_count > 0 else 0.0

        single_game_info = None
        if g_count == 1 and child.games:
            g_obj = child.games[0]
            single_game_info = {
                "white": g_obj.get("white", "Unknown White"),
                "white_elo": g_obj.get("white_elo", 0),
                "black": g_obj.get("black", "Unknown Black"),
                "black_elo": g_obj.get("black_elo", 0),
                "result": g_obj.get("result", "*"),
                "site": g_obj.get("site", ""),
                "moves": g_obj.get("moves", []),
                "opening": g_obj.get("opening", ""),
                "player_color": g_obj.get("player_color", "white"),
            }

        continuations_list.append({
            "san": san_move,
            "uci": child.move_uci,
            "target_fen": child.fen,
            "games_count": g_count,
            "usage_pct": usage_pct,
            "score_pct": score_pct,
            "win_pct": win_pct,
            "draw_pct": draw_pct,
            "loss_pct": loss_pct,
            "wins": w,
            "draws": d,
            "losses": l,
            "single_game_info": single_game_info,
        })

    # Sắp xếp các nước đi tiếp theo theo tần suất chơi (games_count) giảm dần
    continuations_list.sort(key=lambda x: x["games_count"], reverse=True)

    w_node = node.wins
    d_node = node.draws
    node_score = round(((w_node + 0.5 * d_node) / total_at_node) * 100, 1) if total_at_node > 0 else 0.0

    return {
        "fen": fen,
        "in_pgn": True,
        "total_games": total_at_node,
        "wins": w_node,
        "draws": d_node,
        "losses": node.losses,
        "score_pct": node_score,
        "continuations": continuations_list,
    }
