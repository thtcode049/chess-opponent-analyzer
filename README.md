# Chess Opponent Analyzer

> Systems for Analyzing Game Data to Support Chess Match Preparation  
> *Hệ thống phân tích dữ liệu ván đấu hỗ trợ chuẩn bị thi đấu cờ vua*

---

## 📌 Tổng quan dự án (Overview)
**Chess Opponent Analyzer** là ứng dụng Web giúp các kỳ thủ cờ vua phân tích dữ liệu lịch sử thi đấu của đối thủ từ file PGN. Hệ thống tự động trích xuất Repertoire khai cuộc, cây nước đi (Opening Tree), hiệu suất thi đấu (Win rate theo màu quân) và đề xuất các thông tin chuẩn bị trước trận đấu.

---

## 🛠 Công nghệ sử dụng (Tech Stack)
- **Ngôn ngữ chính**: Python 3.11+
- **Giao diện Web**: Streamlit
- **Xử lý cờ vua (PGN/FEN/Moves)**: `python-chess` (`chess`)
- **Xử lý & Thống kê Dữ liệu**: Pandas
- **Trực quan hóa**: Plotly
- **Kiểm thử (Testing)**: Pytest

---

## 🚀 Hướng dẫn cài đặt & Chạy ứng dụng (Installation & Usage)

### 1. Khởi tạo môi trường ảo (Virtual Environment)
```bash
# Trên Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng Streamlit
```bash
streamlit run app.py
```

### 4. Chạy kiểm thử tự động (Unit Tests)
```bash
pytest
```

---

## 📂 Cấu trúc dự án (Project Structure)
```text
chess-opponent-analyzer/
│
├── app.py                      # Giao diện Streamlit chính
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── README.md                   # Tài liệu hướng dẫn dự án
├── .gitignore                  # Cấu hình bỏ qua file trong Git
│
├── data/                       # Dữ liệu ván đấu mẫu và dữ liệu đã xử lý
│   ├── sample.pgn
│   └── processed/
│
├── src/                        # Các module xử lý nghiệp vụ chính
│   ├── __init__.py
│   ├── pgn_parser.py           # Module đọc & parse file PGN
│   ├── opening_tree.py         # Module xây dựng cây khai cuộc (Opening Tree)
│   ├── statistics.py           # Module tính toán thống kê (Win rate, Score)
│   ├── player_profile.py       # Module tổng hợp hồ sơ đối thủ
│   ├── recommendations.py     # Module đề xuất chiến thuật thi đấu
│   └── utils.py                # Module tiện ích dùng chung
│
└── tests/                      # Unit tests kiểm thử các module
    ├── test_pgn_parser.py
    ├── test_opening_tree.py
    └── test_statistics.py
```
