"""
Client networking: chạy ở thread riêng, nhận message từ server và đưa vào callback.
Client GUI có thể sử dụng class này để kết nối và gửi/nhận.
"""
import socket
import threading
from typing import Callable, Optional
import os
import sys

# Khi chạy `python client/gui.py` hoặc `python client/client.py` trực tiếp,
# thư mục gốc dự án không nằm trong sys.path. Thêm parent project vào sys.path
# để import package `common` hoạt động.
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from common.messages import send_msg, recv_json


class ClientConnection:
    """Quản lý kết nối TCP tới server trên thread riêng."""

    def __init__(self, host: str, port: int, player_id: str, on_message: Callable[[dict], None]):
        self.host = host
        self.port = port
        self.player_id = player_id
        self.on_message = on_message
        self.sock: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def _reader_loop(self):
        try:
            while self._running:
                msg = recv_json(self.sock)
                if msg is None:
                    break
                # chuyển đến callback (GUI sẽ xử lý thread-safe bằng queue)
                self.on_message(msg)
        except Exception:
            pass

    def send(self, mtype: str, payload: dict):
        if not self.sock:
            raise RuntimeError('Chưa kết nối')
        try:
            # ĐẢM BẢO luôn gửi player_id
            message = {
                'type': mtype, 
                'payload': payload, 
                'player_id': self.player_id  # LUÔN gửi player_id
            }
            send_msg(self.sock, message)
        except Exception as e:
            # Khi kết nối bị đóng bởi server, báo lại cho caller qua callback
            self._running = False
            try:
                if self.sock:
                    self.sock.close()
            except Exception:
                pass
            # Thông báo lỗi cho GUI/ứng dụng (on_message có thể đưa vào queue)
            try:
                self.on_message({'type': 'ERROR', 'payload': {'msg': f'Connection error: {e}'}})
            except Exception:
                pass
            # Rethrow để caller nếu cần có thể xử lý thêm
            raise

    def close(self):
        self._running = False
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
