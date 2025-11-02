"""
Helper gửi/nhận JSON newline-delimited giữa client và server.
Tất cả chú thích và docstring bằng tiếng Việt để bạn dễ nâng cấp.
"""
import json
import socket
from typing import Optional


def send_msg(sock: socket.socket, obj: dict) -> None:
    """Gửi một message JSON (một dòng) tới socket.

    Args:
        sock: socket đã kết nối
        obj: dict sẽ được chuyển thành JSON
    """
    data = json.dumps(obj, ensure_ascii=False) + "\n"
    sock.sendall(data.encode('utf-8'))


def recv_line(sock: socket.socket) -> Optional[str]:
    """Đọc tới newline, trả về dòng (không có newline). Trả về None khi socket đóng.
    Lưu ý: hàm blocking, nên dùng trong thread hoặc loop phù hợp.
    """
    buf = []
    while True:
        ch = sock.recv(1)
        if not ch:
            return None
        if ch == b"\n":
            break
        buf.append(ch)
    return b"".join(buf).decode('utf-8')


def recv_json(sock: socket.socket) -> Optional[dict]:
    """Đọc một dòng JSON và parse thành dict. Trả về None khi socket đóng.
    """
    line = recv_line(sock)
    if line is None:
        return None
    return json.loads(line)
