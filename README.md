# CaroGame


Một project minh hoạ trò Caro (Gomoku) đa người chơi bằng Python.

##  Cách chơi:

- Kết nối đến máy chủ (nút kết nối)
- Tạo phòng và nhập tên phòng
- Tham gia phòng (client còn lại)
- Sẵn sàng ( 2 client)
- Chơi


Nội dung repository
- `server/` — mã server (socket + threading) quản lý phòng và trạng thái bàn cờ.
- `client/` — client GUI bằng `tkinter` và module kết nối mạng.
- `common/` — helper gửi/nhận JSON newline-delimited.


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

#Mở server và tạo 2 client
python -u main.py

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

## Chạy dự án (chi tiết)

Các bước dưới đây mô tả cách thiết lập môi trường và chạy server & client trên Windows (PowerShell). Nếu bạn trên Linux/macOS, các lệnh tương tự áp dụng nhưng kích hoạt venv khác (ví dụ `source .venv/bin/activate`).

1) Tạo và kích hoạt virtualenv (chỉ lần đầu):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Cài dependencies (nếu có):
```powershell
pip install -r requirements.txt
```

3) Kiểm tra nhanh (tùy chọn):
```powershell
# kiểm tra cú pháp
pythm py_compile server/server.py client/gui.pyon -

# chạy unit tests
python -m unittest discover -v
```

4) Chạy server (mở một cửa sổ PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
python -m server.server
```

5) Chạy client GUI (mở thêm 1 cửa sổ PowerShell cho mỗi client):
```powershell
.\.venv\Scripts\Activate.ps1
python -m client.gui
```

6) Chạy nhiều client: mở thêm các cửa sổ PowerShell và lặp bước 5.

7) Chạy server ở background (tuỳ chọn):
```powershell
# Start a background job (PowerShell)
Start-Job -ScriptBlock { .\.venv\Scripts\Activate.ps1; python -m server.server }

# hoặc Start-Process
Start-Process -NoNewWindow -FilePath python -ArgumentList "-m server.server"
```

8) Nếu port 5000 đang bị chiếm:
```powershell
netstat -ano | Select-String ":5000"
taskkill /PID <PID> /F
```

9) Run scripts (nếu có):
- Nếu repo có `run-server.ps1` hoặc `run-client.ps1`, bạn chỉ cần chạy `.
un-server.ps1` hoặc `.
un-client.ps1` để tự động kích hoạt venv và khởi server/client.

10) Tắt virtualenv khi xong:
```powershell
deactivate
```

Mẹo: Luôn `git fetch` / `git pull --rebase origin main` trước khi tạo branch mới để tránh xung đột.
<<<<<<< HEAD
# CaroGame (Multi Client-Server) - Hướng dẫn nhanh (tiếng Việt)

Mục tiêu: một server Python quản lý nhiều phòng Caro (5-in-a-row). Client GUI dùng tkinter.

Chuẩn bị
- Python 3.8+

Cấu trúc
- server/
  - `server.py` - entrypoint server
  - `game.py` - logic phòng và kiểm tra thắng
- client/
  - `gui.py` - client GUI tkinter
  - `client.py` - wrapper kết nối mạng (chạy ở thread riêng)
- common/
  - `messages.py` - helper gửi/nhận JSON per-line
- main.py - mở server và tạo 2 client

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
