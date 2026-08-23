"""
Gemini AI Client Module
-----------------------
Chức năng: Giao tiếp với Google Gemini API (gemini-3.5-flash / gemini-3.1-flash-lite / gemini-3.1-pro-preview)
để thực hiện suy luận thông minh, trả lời hội thoại phân tích đối thủ dựa trên dữ liệu Profile & Opening Tree.
Hỗ trợ Server-Side Built-in Key, Streaming Response (st.write_stream) và Chế độ Phản hồi Dự phòng khi ngoại tuyến.
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Generator, Optional

from src.ai_assistant.config import get_server_gemini_api_key
from src.ai_assistant.local_expert import generate_local_expert_response

# Danh sách Model hiển thị cho người dùng lựa chọn (Đã xác minh hoạt động 100%)
AVAILABLE_MODELS = {
    "gemini-3.5-flash": "Gemini 3.5 Flash ⚡ (Tốc độ cao & Suy luận sắc bén)",
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite 🚀 (Phản hồi tức thì)",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro 🧠 (Đại kiện tướng Phân tích sâu)",
}

GEMINI_MODELS = list(AVAILABLE_MODELS.keys())

SYSTEM_INSTRUCTION = """Bạn là Đại kiện tướng Cờ vua kiêm Chuyên gia Phân tích Dữ liệu Đối thủ (Chess Opponent AI Analyst).

NHIỆM VỤ CỦA BẠN:
1. Bạn có vai trò như một trợ lý AI thông minh, đàm thoại tự nhiên, sắc sảo, trả lời mọi câu hỏi của người dùng về đối thủ cờ vua.
2. Nền tảng phân tích của bạn dựa trên 100% DỮ LIỆU THỰC NGHIỆM được cung cấp trong phần NGỮ CẢNH (Bao gồm Profile đối thủ, Danh mục Khai cuộc Repertoire, Cấu trúc Tốt, Phong cách thi đấu 6 chiều, Độ chính xác từng Giai đoạn, và Cây Khai cuộc Opening Tree).
3. Hãy trả lời cụ thể, logic, trích dẫn các con số thực tế (số ván, tỷ lệ thắng/hòa/thua, điểm số hiệu chỉnh Bayesian, độ lệch Delta, nhãn đánh giá độ tin cậy Confirmed Strength/Weakness).
4. Bạn có thể đưa ra các lời khuyên chiến thuật tác chiến sắc bén, gợi ý các biến khai cuộc nên chơi hoặc nên tránh dựa trên dữ liệu.
5. Trình bày bằng Tiếng Việt tự nhiên, chuẩn mực, sử dụng định dạng Markdown (tiêu đề, gạch đầu dòng, bảng số liệu nếu cần). Giữ nguyên các thuật ngữ cờ vua chuyên dụng ngắn gọn (như ECO, PGN, FEN, Blitz, Rapid, Bullet, Classical, Depth, ACPL, Stockfish, Win Rate, Draw Rate, Loss Rate, Score...).
"""


def _prepare_gemini_payload(prompt: str, context: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Chuẩn bị payload JSON gửi tới Gemini API."""
    contents = []

    # 1. System Context Block
    system_text = f"{SYSTEM_INSTRUCTION}\n\n=== DỮ LIỆU NGỮ CẢNH ĐỐI THỦ ===\n{context}\n================================"
    contents.append({
        "role": "user",
        "parts": [{"text": system_text}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": "Tôi đã nắm rõ toàn bộ dữ liệu thống kê đối thủ và sẵn sàng phân tích, trả lời mọi câu hỏi của bạn."}]
    })

    # 2. Lịch sử hội thoại
    for msg in chat_history[-8:]:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}]
        })

    # 3. Tin nhắn người dùng hiện tại
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    return {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "topP": 0.9,
            "maxOutputTokens": 2048,
        }
    }


def stream_gemini_response(
    prompt: str,
    context: str,
    chat_history: List[Dict[str, str]],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    deep_profile: Optional[Dict[str, Any]] = None,
    stats: Optional[Dict[str, Any]] = None,
    fen_map_white: Optional[Dict[str, Any]] = None,
    fen_map_black: Optional[Dict[str, Any]] = None,
    selected_player: str = "Đối thủ"
) -> Generator[str, None, None]:
    """
    Generator phản hồi dạng Stream (chữ chạy từng từ mượt mà như ChatGPT / Gemini).
    """
    clean_key = (api_key if api_key is not None else get_server_gemini_api_key()).strip()
    target_model = model if model in GEMINI_MODELS else "gemini-3.5-flash"

    # Nếu không có API Key máy chủ, tự động dùng Local Expert Engine stream từng câu/đoạn
    if not clean_key:
        fallback_text = generate_local_expert_response(
            prompt=prompt,
            deep_profile=deep_profile,
            stats=stats,
            fen_map_white=fen_map_white,
            fen_map_black=fen_map_black,
            selected_player=selected_player
        )
        words = fallback_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
        return

    payload = _prepare_gemini_payload(prompt, context, chat_history)
    models_to_try = [target_model] + [m for m in GEMINI_MODELS if m != target_model]

    streamed_anything = False
    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:streamGenerateContent?alt=sse&key={clean_key}"
        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                for line in resp:
                    decoded_line = line.decode("utf-8")
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:].strip()
                        if not json_str:
                            continue
                        try:
                            chunk_json = json.loads(json_str)
                            candidates = chunk_json.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text_piece = part.get("text", "")
                                    if text_piece:
                                        streamed_anything = True
                                        yield text_piece
                        except Exception:
                            continue
            if streamed_anything:
                return
        except Exception:
            continue

    # Nếu tất cả các model cloud đều lỗi, fallback sang local expert
    fallback_text = generate_local_expert_response(
        prompt=prompt,
        deep_profile=deep_profile,
        stats=stats,
        fen_map_white=fen_map_white,
        fen_map_black=fen_map_black,
        selected_player=selected_player
    )
    words = fallback_text.split(" ")
    for i in range(0, len(words), 3):
        chunk = " ".join(words[i:i+3]) + " "
        yield chunk


def call_gemini_api(
    prompt: str,
    context: str,
    chat_history: List[Dict[str, str]],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    deep_profile: Optional[Dict[str, Any]] = None,
    stats: Optional[Dict[str, Any]] = None,
    fen_map_white: Optional[Dict[str, Any]] = None,
    fen_map_black: Optional[Dict[str, Any]] = None,
    selected_player: str = "Đối thủ"
) -> str:
    """
    Gọi Gemini API lấy toàn bộ câu trả lời dạng văn bản (Non-streaming).
    """
    clean_key = (api_key if api_key is not None else get_server_gemini_api_key()).strip()
    target_model = model if model in GEMINI_MODELS else "gemini-3.5-flash"

    if not clean_key:
        return generate_local_expert_response(
            prompt=prompt,
            deep_profile=deep_profile,
            stats=stats,
            fen_map_white=fen_map_white,
            fen_map_black=fen_map_black,
            selected_player=selected_player
        )

    payload = _prepare_gemini_payload(prompt, context, chat_history)
    models_to_try = [target_model] + [m for m in GEMINI_MODELS if m != target_model]

    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={clean_key}"
        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                if resp.status == 200:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    candidates = resp_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
        except Exception:
            continue

    return generate_local_expert_response(
        prompt=prompt,
        deep_profile=deep_profile,
        stats=stats,
        fen_map_white=fen_map_white,
        fen_map_black=fen_map_black,
        selected_player=selected_player
    )
