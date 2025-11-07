import threading
import subprocess
import sys
import time
import os


# File này để mở server và tạo 2 client GUI trong các process riêng biệt.

def _run_server():
	# Import inside the thread target to ensure module path is set up correctly
	from server.server import main as server_main
	server_main()


def main():
	# Start server in a background daemon thread
	server_thread = threading.Thread(target=_run_server, daemon=True)
	server_thread.start()

	# Give server a moment to bind the port
	time.sleep(0.6)

	# Launch two client GUI processes
	python_exe = sys.executable or "python"
	clients = []
	for _ in range(2):
		p = subprocess.Popen([python_exe, "-m", "client.gui"], cwd=os.path.dirname(os.path.abspath(__file__)))
		clients.append(p)

	# Wait for both clients to exit; when they do, allow process to finish (daemon server thread will stop)
	for p in clients:
		try:
			p.wait()
		except KeyboardInterrupt:
			break

	# Optional: attempt to terminate remaining clients on exit
	for p in clients:
		if p.poll() is None:
			try:
				p.terminate()
			except Exception:
				pass


if __name__ == "__main__":
	main()