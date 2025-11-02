# CaroGame

Một project minh hoạ trò Caro (Gomoku) đa người chơi bằng Python.

Nội dung repository
- `server/` — mã server (socket + threading) quản lý phòng và trạng thái bàn cờ.
- `client/` — client GUI bằng `tkinter` và module kết nối mạng.
- `common/` — helper gửi/nhận JSON newline-delimited.
- `tests/` — unit tests cho logic game.

Yêu cầu
- Python 3.8+

Cài đặt nhanh (Windows / PowerShell)
```powershell
# clone repo
git clone https://github.com/HuyDev19/CaroGame.git
cd CaroGame

# tạo virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# cài dependencies (nếu có file requirements.txt)
pip install -r requirements.txt
```

Chạy server và client
```powershell
# Trong terminal 1: chạy server
python -m server.server

# Trong terminal 2: chạy client GUI
python -m client.gui
```

Chạy tests
```powershell
python -m unittest discover -v
```

Quy tắc làm việc nhóm (ngắn gọn)
- Tạo branch cho mỗi feature/bug: `git checkout -b feature/ten-feature`.
- Commit với message rõ ràng: `feat: ...`, `fix: ...`, `chore: ...`.
- Push branch lên remote và tạo Pull Request để review trước khi merge.

Loại trừ file không cần thiết
- Đã thêm `.gitignore` để bỏ qua `__pycache__/` và `*.pyc`.

Muốn đóng góp
- Fork hoặc được thêm vào repo như collaborator.
- Mở PR từ branch của bạn vào `main` (kèm mô tả và test nếu thay đổi logic).

Liên hệ
- Nếu cần hỗ trợ, mở issue trên GitHub hoặc liên hệ chủ repo.

---
Tài liệu này là hướng dẫn cơ bản để nhanh chóng chạy và đóng góp cho dự án.
<<<<<<< HEAD
# CaroGame (Multi Client-Server) - Hướng dẫn nhanh (tiếng Việt)

Mục tiêu: một server Python quản lý nhiều phòng Caro (5-in-a-row). Client GUI dùng tkinter.

Chuẩn bị
- Python 3.8+
- Không cần thư viện bên ngoài (dùng stdlib)

Cấu trúc
- server/
  - `server.py` - entrypoint server
  - `game.py` - logic phòng và kiểm tra thắng
- client/
  - `gui.py` - client GUI tkinter
  - `client.py` - wrapper kết nối mạng (chạy ở thread riêng)
- common/
  - `messages.py` - helper gửi/nhận JSON per-line
- tests/
  - `test_game.py` - test logic thắng

Chạy server (PowerShell):
```powershell
python server/server.py
```

Chạy client (mở 2 cửa sổ để test 2 người):
```powershell
python client/gui.py
```

Giao thức: newline-delimited JSON, message có trường `type` and `payload`.

Ghi chú thiết kế: tất cả trạng thái trò chơi được validate và cập nhật ở server.
=======
# CaroGame
>>>>>>> 5951ecb771af268f7b47b567fcf1ef5bee65be8e
