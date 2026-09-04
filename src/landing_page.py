"""
Landing Page Module
-------------------
Chức năng: Cung cấp giao diện Trang chủ (Landing Page) độc lập giới thiệu phần mềm
Chess Opponent Analyzer với phong cách chuyên nghiệp, tối giản, chuẩn phần mềm phân tích dữ liệu cờ vua.
"""

import streamlit as st
from src.ui_components import get_icon_svg


def render_landing_page(on_start_analysis):
    """
    Render toàn bộ giao diện Trang chủ (Landing Page).
    """
    # Custom CSS cho Landing Page
    st.markdown("""
    <style>
        /* Smooth scrolling & global resets */
        html {
            scroll-behavior: smooth;
        }
        body, .stApp {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        /* Sticky Navigation Header */
        .landing-header {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid #e2e8f0;
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: -1rem;
            margin-bottom: 2rem;
            border-radius: 8px;
        }
        .landing-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
            text-decoration: none;
        }
        .landing-nav-links {
            display: flex;
            gap: 24px;
            font-size: 14px;
            font-weight: 600;
        }
        .landing-nav-links a {
            color: #475569;
            text-decoration: none;
            transition: color 0.15s ease;
        }
        .landing-nav-links a:hover {
            color: #4f46e5;
        }

        /* Hero Section */
        .hero-headline {
            font-size: 36px;
            font-weight: 800;
            line-height: 1.25;
            color: #0f172a;
            margin-bottom: 12px;
        }
        .hero-tagline {
            font-size: 15px;
            font-weight: 700;
            color: #4f46e5;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 8px;
        }
        .hero-desc {
            font-size: 16px;
            line-height: 1.6;
            color: #475569;
            margin-bottom: 24px;
        }

        /* Product Mockup Preview Container */
        .mockup-container {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        }
        .mockup-header {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #f1f5f9;
        }
        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        /* Card Styles */
        .landing-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 16px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .landing-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.06);
            border-color: #c7d2fe;
        }
        .card-icon {
            font-size: 24px;
            margin-bottom: 10px;
            color: #4f46e5;
        }
        .card-title {
            font-size: 17px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 6px;
        }
        .card-desc {
            font-size: 14px;
            color: #64748b;
            line-height: 1.5;
        }

        /* Pipeline Flow Diagram */
        .pipeline-flow {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 20px 16px;
            margin: 24px 0;
            flex-wrap: wrap;
            gap: 10px;
        }
        .pipeline-step {
            background-color: #f1f5f9;
            border: 1px solid #cbd5e1;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 700;
            color: #1e293b;
            text-align: center;
        }
        .pipeline-arrow {
            color: #4f46e5;
            font-weight: 800;
            font-size: 18px;
        }

        /* How it works steps */
        .step-num {
            font-size: 28px;
            font-weight: 900;
            color: #4f46e5;
            margin-bottom: 4px;
        }

        /* CTA Section */
        .cta-box {
            text-align: center;
            background-color: #ffffff;
            border: 1px solid #c7d2fe;
            border-radius: 14px;
            padding: 40px 24px;
            margin: 40px 0;
            box-shadow: 0 10px 30px -10px rgba(79, 70, 229, 0.1);
        }
        .cta-title {
            font-size: 26px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 8px;
        }

        /* Footer */
        .landing-footer {
            border-top: 1px solid #e2e8f0;
            padding: 24px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #64748b;
            font-size: 13px;
            margin-top: 40px;
        }
    </style>
    """, unsafe_allow_html=True)

    # 1. HEADER (Sticky Navigation Header)
    st.markdown("""
    <div class="landing-header">
        <div class="landing-brand">
            <span style="font-size:22px;">♟</span> Chess Player Analyzer
        </div>
        <div class="landing-nav-links">
            <a href="#sec-features">Tính năng</a>
            <a href="#sec-pipeline">Quy trình Xử lý Dữ liệu</a>
            <a href="#sec-how">Cách thức Hoạt động</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. HERO SECTION (2 Columns)
    col_hero_text, col_hero_mockup = st.columns([5, 6])

    with col_hero_text:
        st.markdown("""
        <div style="padding-top:10px;">
            <div class="hero-tagline">NỀN TẢNG PHÂN TÍCH & HUẤN LUYỆN CỜ VUA THÔNG MINH</div>
            <div class="hero-headline">Thấu hiểu phong độ kỳ thủ.<br>Rèn luyện bản thân & Khắc chế đối thủ.</div>
            <div class="hero-desc">Biến dữ liệu ván đấu PGN thành cây khai cuộc trực quan, đánh giá độ chính xác từng giai đoạn và nhận định chiến lược cùng Đại kiện tướng AI.</div>
        </div>
        """, unsafe_allow_html=True)

        b1, b2 = st.columns([5, 5])
        with b1:
            if st.button("🎯 Bắt đầu Phân tích", key="hero_start_analysis_btn", use_container_width=True):
                on_start_analysis()
        with b2:
            st.markdown("""
            <a href="#sec-features" style="text-decoration:none;">
                <div style="text-align:center; padding:6px 12px; border:1px solid #cbd5e1; border-radius:5px; font-weight:600; font-size:13px; color:#475569; background:#fff;">
                    🔍 Khám phá Tính năng
                </div>
            </a>
            """, unsafe_allow_html=True)

    with col_hero_mockup:
        st.markdown("""
        <div class="mockup-container">
            <div class="mockup-header">
                <div class="dot" style="background:#ef4444;"></div>
                <div class="dot" style="background:#eab308;"></div>
                <div class="dot" style="background:#22c55e;"></div>
                <span style="font-size:11px; color:#94a3b8; font-weight:600; margin-left:8px;">Chess Opponent Analyzer — Product Preview</span>
            </div>
            <div style="display:flex; gap:12px;">
                <div style="width:45%; background:#1e293b; height:170px; border-radius:6px; display:flex; align-items:center; justify-content:center; color:#94a3b8; font-size:32px;">
                    ♟️
                </div>
                <div style="width:55%;">
                    <div style="font-size:12px; font-weight:700; color:#475569; margin-bottom:4px;">Opening Tree Continuations</div>
                    <div style="background:#f1f5f9; padding:6px 8px; border-radius:4px; font-size:11px; margin-bottom:4px; display:flex; justify-content:space-between;">
                        <span>▶ 1...c5 (Sicilian)</span>
                        <span style="font-weight:700;">56 games</span>
                    </div>
                    <div style="display:flex; height:10px; width:100%; border-radius:3px; overflow:hidden; margin-bottom:8px;">
                        <div style="width:59.8%; background:#22c55e;" title="Win"></div>
                        <div style="width:20%; background:#64748b;" title="Draw"></div>
                        <div style="width:20.2%; background:#ef4444;" title="Loss"></div>
                    </div>
                    <div style="font-size:11px; background:#eff6ff; border-left:3px solid #3b82f6; padding:6px; border-radius:3px; color:#1e40af;">
                        <b>Insight:</b> Opponent scores 59.8% in Sicilian. Prepare 2.c3 Alapin.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:48px;'></div>", unsafe_allow_html=True)

    # 3. FEATURES SECTION ("Phân tích được những gì?")
    st.markdown("<h3 id='sec-features' style='text-align:center; margin-bottom:24px;'>Phân tích được những gì?</h3>", unsafe_allow_html=True)

    tree_icon = get_icon_svg("tree", size=24)
    stats_icon = get_icon_svg("stats", size=24)
    profile_icon = get_icon_svg("profile", size=24)
    prep_icon = get_icon_svg("prep", size=24)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown(f"""
        <div class="landing-card">
            <div class="card-icon">{tree_icon}</div>
            <div class="card-title">Cây Khai Cuộc Trực Quan</div>
            <div class="card-desc">Khám phá mọi biến thể khai cuộc đối thủ từng chơi, kèm tỷ lệ thắng/hòa/thua và hiệu suất trên từng nước đi.</div>
        </div>
        """, unsafe_allow_html=True)
    with f2:
        st.markdown(f"""
        <div class="landing-card">
            <div class="card-icon">{stats_icon}</div>
            <div class="card-title">Thống Kê Hiệu Suất Toàn Diện</div>
            <div class="card-desc">Đo lường tỉ lệ thắng cầm Trắng/Đen, hiệu suất theo từng hệ thống khai cuộc và phát hiện biến cờ yếu nhất.</div>
        </div>
        """, unsafe_allow_html=True)
    with f3:
        st.markdown(f"""
        <div class="landing-card">
            <div class="card-icon">{profile_icon}</div>
            <div class="card-title">Hồ Sơ Phong Cách & Thói Quen</div>
            <div class="card-desc">Tự động nhận diện nước đi ưa thích, phản ứng quen thuộc trước 1.e4/1.d4 và xu hướng chiến thuật của kỳ thủ.</div>
        </div>
        """, unsafe_allow_html=True)
    with f4:
        st.markdown(f"""
        <div class="landing-card">
            <div class="card-icon">{prep_icon}</div>
            <div class="card-title">Trợ Lí AI & Kế Hoạch Chiến Lược</div>
            <div class="card-desc">Bản tóm tắt suy luận mở đầu và đàm thoại cùng Đại kiện tướng AI để lập giáo án hoặc kế hoạch thi đấu.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:36px;'></div>", unsafe_allow_html=True)

    # 4. DATA TO INSIGHT PIPELINE SECTION ("From Games to Insights")
    st.markdown("<h3 id='sec-pipeline' style='text-align:center; margin-bottom:16px;'>Quy trình Xử lý Dữ liệu</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class="pipeline-flow">
        <div class="pipeline-step">PGN DATA</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step">OPENING TREE</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step">PERFORMANCE ANALYSIS</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step">PLAYER INSIGHTS</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step" style="background:#e0e7ff; border-color:#818cf8; color:#3730a3;">AI STRATEGIC COACHING</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:36px;'></div>", unsafe_allow_html=True)

    # 5. EXAMPLE SECTION ("Từ dữ liệu đến quyết định")
    st.markdown("<h3 style='text-align:center; margin-bottom:20px;'>Từ Dữ Liệu Đến Quyết Định Chiến Thuật</h3>", unsafe_allow_html=True)

    ex1, ex2 = st.columns(2)
    with ex1:
        st.markdown("""
        <div class="landing-card">
            <div style="font-size:12px; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:8px;">Dữ liệu thô PGN</div>
            <div style="font-size:24px; font-weight:800; color:#0f172a; margin-bottom:8px;">119 Games</div>
            <div style="font-size:14px; color:#475569; line-height:1.6;">
                • 56 Black games<br>
                • 25 Wins (44.6%)<br>
                • 17 Draws (30.4%)<br>
                • 14 Losses (25.0%)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ex2:
        st.markdown("""
        <div class="landing-card" style="border-left:4px solid #4f46e5;">
            <div style="font-size:12px; font-weight:700; color:#4f46e5; text-transform:uppercase; margin-bottom:8px;">Nhận định Tự động</div>
            <div style="font-size:14px; color:#1e293b; font-weight:600; margin-bottom:6px;">"Player frequently plays this opening."</div>
            <div style="font-size:13px; color:#475569; margin-bottom:4px;">Most common response: <b>1...c6 (Caro-Kann)</b></div>
            <div style="font-size:13px; color:#d97706; font-weight:700; margin-bottom:12px;">Score: 59.8%</div>
            
            <div style="font-size:12px; font-weight:700; color:#059669; text-transform:uppercase; margin-bottom:4px;">Kế hoạch Hành động</div>
            <div style="font-size:13px; color:#047857; background:#ecfdf5; padding:8px 12px; border-radius:6px;">
                Tập trung nghiên cứu 2.d4 d5 3.f3 (Fantasy Variation) để khai thác lỗ hổng đạt điểm số 38%.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:36px;'></div>", unsafe_allow_html=True)

    # 6. HOW IT WORKS SECTION ("3 bước")
    st.markdown("<h3 id='sec-how' style='text-align:center; margin-bottom:24px;'>3 Bước Đơn Giản</h3>", unsafe_allow_html=True)

    h1, h2, h3 = st.columns(3)
    with h1:
        st.markdown("""
        <div class="landing-card" style="text-align:center;">
            <div class="step-num">01</div>
            <div class="card-title">Nạp Dữ Liệu</div>
            <div class="card-desc">Tải lên file PGN hoặc nạp trực tiếp từ Lichess/Chess.com.</div>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown("""
        <div class="landing-card" style="text-align:center;">
            <div class="step-num">02</div>
            <div class="card-title">Phân Tích Kỳ Thủ</div>
            <div class="card-desc">Xem cây khai cuộc, thống kê phong độ và hồ sơ nhận định tự động.</div>
        </div>
        """, unsafe_allow_html=True)
    with h3:
        st.markdown("""
        <div class="landing-card" style="text-align:center;">
            <div class="step-num">03</div>
            <div class="card-title">Trợ Lí AI Đồng Hành</div>
            <div class="card-desc">Nhận bản suy luận mở đầu và đàm thoại chiến lược cùng Đại kiện tướng AI.</div>
        </div>
        """, unsafe_allow_html=True)

    # 7. CTA SECTION
    st.markdown("""
    <div class="cta-box">
        <div class="cta-title">Sẵn sàng nâng cao trình độ cờ vua?</div>
        <div style="font-size:15px; color:#475569; margin-bottom:20px;">Bắt đầu phân tích kỳ thủ ngay bây giờ hoàn toàn miễn phí.</div>
    </div>
    """, unsafe_allow_html=True)

    c_center1, c_center2, c_center3 = st.columns([3, 4, 3])
    with c_center2:
        if st.button("🚀 Bắt đầu Phân tích →", key="cta_start_analysis_btn", use_container_width=True):
            on_start_analysis()

    # 8. FOOTER
    st.markdown("""
    <div class="landing-footer">
        <div>
            <b>♟ Chess Player Analyzer</b> — Nền tảng Phân tích & Huấn luyện Cờ vua Thông minh
        </div>
        <div>
            Built with Streamlit & python-chess
        </div>
    </div>
    """, unsafe_allow_html=True)
