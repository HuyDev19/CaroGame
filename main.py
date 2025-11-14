import threading
import subprocess
import sys
import time
import os


# File này để mở server và tạo 2 client GUI trong các process riêng biệt.

def _run_server():
	# Nhập vào mục tiêu luồng để đảm bảo đường dẫn mô-đun được thiết lập chính xác
	from server.server import main as server_main
	server_main()


def main():
	# Khởi động máy chủ trong luồng nền của daemon
	server_thread = threading.Thread(target=_run_server, daemon=True)
	server_thread.start()

	# Cho máy chủ một chút thời gian để liên kết cổng
	time.sleep(0.6)

	# Khởi chạy hai tiến trình GUI của máy khách
	python_exe = sys.executable or "python"
	clients = []
	for _ in range(2):
		p = subprocess.Popen([python_exe, "-m", "client.gui"], cwd=os.path.dirname(os.path.abspath(__file__)))
		clients.append(p)

	# Chờ cả hai máy khách thoát; khi chúng thoát, hãy cho phép tiến trình kết thúc (luồng máy chủ daemon sẽ dừng)
	for p in clients:
		try:
			p.wait()
		except KeyboardInterrupt:
			break

	# Tùy chọn: cố gắng chấm dứt các máy khách còn lại khi thoát
	for p in clients:
		if p.poll() is None:
			try:
				p.terminate()
			except Exception:
				pass


if __name__ == "__main__":
	main()