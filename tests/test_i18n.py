from src.i18n import t, TRANSLATIONS


def test_t_function_default_vietnamese():
    res_vi = t("app_title", lang="vi")
    assert res_vi == "Chess Opponent Analyzer"
    
    res_vi_format = t("total_games_analyzed", lang="vi", count=50)
    assert "50" in res_vi_format
    assert "Tổng số ván đã phân tích" in res_vi_format


def test_t_function_english():
    res_en = t("app_subtitle", lang="en")
    assert res_en == "Analyze your opponent. Prepare with confidence."

    res_en_format = t("total_games_analyzed", lang="en", count=50)
    assert "50" in res_en_format
    assert "Total Games Analyzed" in res_en_format


def test_missing_key_fallback():
    res = t("non_existent_key_xyz", lang="en")
    assert res == "non_existent_key_xyz"

