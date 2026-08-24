import pytest
from src.ai_assistant.context_builder import build_opponent_ai_context, summarize_opening_tree
from src.ai_assistant.gemini_client import call_gemini_api, stream_gemini_response, GEMINI_MODELS
from src.ai_assistant.local_expert import generate_local_expert_response
from src.opening_tree import build_opening_tree


def test_build_opponent_ai_context_empty():
    res = build_opponent_ai_context(None, None)
    assert "chưa có dữ liệu" in res.lower()


def test_build_opponent_ai_context_valid():
    stats = {
        "total_games": 20,
        "wins": 10,
        "draws": 4,
        "losses": 6,
        "win_rate": 50.0,
        "draw_rate": 20.0,
        "loss_rate": 30.0,
        "score_percentage": 60.0,
        "white_games": 10,
        "white_score_percentage": 70.0,
        "white_wins": 7,
        "white_draws": 0,
        "white_losses": 3,
        "black_games": 10,
        "black_score_percentage": 50.0,
        "black_wins": 3,
        "black_draws": 4,
        "black_losses": 3,
    }
    deep_profile = {
        "repertoire": {
            "white_repertoire": [
                {
                    "name": "Sicilian Defense",
                    "games_count": 8,
                    "wins": 5,
                    "draws": 2,
                    "losses": 1,
                    "score_pct": 75.0,
                    "adjusted_score_pct": 71.0,
                    "delta_vs_baseline": 11.0,
                    "assessment_badge": "Thế mạnh đã xác nhận",
                }
            ],
            "black_repertoire": []
        },
        "style_profile": {
            "is_simplifier": True,
            "avg_endgame_move": 25.0,
            "raw_metrics": {
                "complexity_index": 78.0,
                "volatility_score": 65.0,
                "sacrifice_rate": 20.0,
                "total_sacrifices": 2,
                "simplification_rate": 40.0,
                "resilience_rate": 60.0,
                "closed_preference": 45.0,
                "open_preference": 55.0
            },
            "evidence": ["Độ biến động chiến thuật cao", "Xác nhận đặc trưng Simplifier"]
        },
        "phases": {
            "phases": {
                "opening": {"accuracy": 91.2, "games_count": 20, "analyzed_moves": 160},
                "middlegame": {"accuracy": 82.4, "games_count": 20, "analyzed_moves": 240},
                "endgame": {"accuracy": 76.0, "games_count": 12, "analyzed_moves": 120}
            }
        },
        "structures": {
            "structures": [
                {
                    "name": "Carlsbad",
                    "games_count": 5,
                    "wins": 1,
                    "draws": 1,
                    "losses": 3,
                    "score_pct": 30.0,
                    "adjusted_score_pct": 36.0,
                    "delta_vs_baseline": -24.0,
                    "assessment_badge": "Điểm yếu đã xác nhận",
                    "typical_move": "12"
                }
            ]
        }
    }

    ctx = build_opponent_ai_context(deep_profile, stats, selected_player="Magnus")
    assert "BÁO CÁO DỮ LIỆU THỰC NGHIỆM ĐỐI THỦ: MAGNUS" in ctx
    assert "Simplifier" in ctx
    assert "Carlsbad" in ctx
    assert "Sicilian Defense" in ctx
    assert "91.2%" in ctx
    assert "78.0" in ctx

    # Test sample warning in context
    ctx_sample = build_opponent_ai_context(
        deep_profile, stats, selected_player="Magnus",
        analyzed_games_count=5, total_games_count=20
    )
    assert "CẢNH BÁO ĐỘ TIN CẬY DỮ LIỆU ĐÁNH GIÁ NƯỚC ĐI" in ctx_sample
    assert "5/20 ván" in ctx_sample


def test_local_expert_response():
    stats = {"total_games": 20, "score_percentage": 60.0}
    deep_profile = {
        "repertoire": {"white_repertoire": [{"name": "Sicilian Defense", "games_count": 8, "score_pct": 75.0, "wins": 5, "draws": 2, "losses": 1}]},
        "structures": {"structures": [{"name": "Carlsbad", "games_count": 5, "score_pct": 30.0, "adjusted_score_pct": 36.0, "delta_vs_baseline": -24.0, "wins": 1, "draws": 1, "losses": 3, "assessment_badge": "Điểm yếu", "typical_move": "12"}]},
        "style_profile": {"primary_style": "Tactical", "raw_metrics": {}},
        "phases": {"phases": {}},
        "simplification": {}
    }
    resp = generate_local_expert_response("Khai cuộc của đối thủ thế nào?", deep_profile, stats, selected_player="Magnus")
    assert "Khai cuộc" in resp or "Repertoire" in resp

    resp_struct = generate_local_expert_response("Cấu trúc Tốt đối thủ chơi ra sao?", deep_profile, stats, selected_player="Magnus")
    assert "Cấu trúc" in resp_struct or "Carlsbad" in resp_struct


def test_call_gemini_api_fallback_when_no_key():
    stats = {
        "total_games": 20, "wins": 10, "draws": 4, "losses": 6,
        "win_rate": 50.0, "draw_rate": 20.0, "loss_rate": 30.0,
        "score_percentage": 60.0, "white_games": 10, "white_score_percentage": 70.0,
        "black_games": 10, "black_score_percentage": 50.0,
    }
    deep_profile = {
        "repertoire": {"white_repertoire": [], "black_repertoire": []},
        "style_profile": {"primary_style": "Solid / Universal"},
        "phases": {"phases": {}},
        "structures": {"structures": []},
        "simplification": {}
    }
    resp = call_gemini_api(
        prompt="Khai cuộc của đối thủ thế nào?",
        context="Kỳ thủ Magnus Carlsen.",
        chat_history=[],
        api_key="",
        deep_profile=deep_profile,
        stats=stats,
        selected_player="Magnus"
    )
    assert "Khai cuộc" in resp or "Repertoire" in resp or "Magnus" in resp


def test_stream_gemini_response_fallback():
    stats = {"total_games": 20, "score_percentage": 60.0}
    deep_profile = {
        "repertoire": {"white_repertoire": []},
        "structures": {"structures": []},
        "style_profile": {"primary_style": "Tactical", "raw_metrics": {}},
        "phases": {"phases": {}},
        "simplification": {}
    }
    chunks = list(stream_gemini_response(
        prompt="Tóm tắt đối thủ",
        context="Data",
        chat_history=[],
        api_key="",
        deep_profile=deep_profile,
        stats=stats,
        selected_player="Magnus"
    ))
    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert "Báo cáo" in full_text or "Magnus" in full_text
