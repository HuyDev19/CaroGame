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
