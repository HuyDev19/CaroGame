"""
Server đơn giản dùng socket + threading để quản lý nhiều client.
Giao thức: newline-delimited JSON, dùng helper trong `common/messages.py`.

Chú ý: mã này nhằm mục đích minh hoạ cho bài giữa kỳ. Bạn có thể mở rộng
thêm authentication, timeout, heartbeat, và persistent storage.
"""
import threading
import socket
import json
from typing import Dict
import traceback
import os
import sys

# Nếu chạy trực tiếp `python server/server.py`, thư mục dự án cha cần được thêm vào
# sys.path để import package `common`/`client` được (vì các module nằm song song với `server`).
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from common.messages import send_msg, recv_json
from server.game import Room

HOST = '0.0.0.0'
PORT = 5000

# rooms: room_id -> Room
rooms: Dict[str, Room] = {}
# danh sách mọi kết nối client hiện tại (để broadcast toàn cục cập nhật danh sách phòng)
clients = set()


def broadcast_room(room: Room, msg: dict) -> None:
    """Gửi msg (dict) tới tất cả client trong phòng (nếu socket còn kết nối)."""
    for pid, sock in list(room.players.items()):
        try:
            send_msg(sock, msg)
        except Exception:
            print(f"Lỗi khi gửi tới {pid}, xoá player")
            try:
                sock.close()
            except Exception:
                pass
            room.remove_player(pid)


def broadcast_all(msg: dict) -> None:
    """Gửi msg tới tất cả client đang kết nối (ở bất kỳ phòng nào)."""
    for c in list(clients):
        try:
            send_msg(c, msg)
        except Exception:
            try:
                c.close()
            except Exception:
                pass
            try:
                clients.remove(c)
            except Exception:
                pass


def build_rooms_list() -> list:
    res = []
    for rid, r in rooms.items():
        res.append({'room': rid, 'players': len(r.players), 'creator': r.creator})
    return res

def handle_client(conn: socket.socket, addr):
    """Hàm chạy trên thread cho mỗi client kết nối.
    Client gửi JSON: {"type":..., "payload": {...}, "player_id":...}
    """
    print(f"Client từ {addr} kết nối")
    # thêm vào danh sách client toàn cục
    try:
        clients.add(conn)
    except Exception:
        pass
    player_id = None
    current_room = None
    try:
        while True:
            msg = recv_json(conn)
            if msg is None:
                print(f"Client {addr} đóng kết nối")
                break
            mtype = msg.get('type')
            payload = msg.get('payload', {})
            player_id = msg.get('player_id') or player_id

            if mtype == 'CREATE_ROOM':
                room_id = payload.get('room')
                if not room_id:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Missing room id'}})
                    continue
                if room_id in rooms:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room exists'}})
                    continue
                # Thiết lập creator là player_id (nếu client cung cấp) hoặc port
                creator = player_id or str(addr[1])
                room = Room(room_id, creator=creator)
                rooms[room_id] = room
                room.add_player(player_id or str(addr[1]), conn)
                current_room = room
                send_msg(conn, {'type': 'ROOM_CREATED', 'payload': {'room': room_id}})
                # thông báo cập nhật danh sách phòng cho tất cả client
                broadcast_all({'type': 'LIST_ROOMS_RESPONSE', 'payload': {'rooms': build_rooms_list()}})

            elif mtype == 'JOIN_ROOM':
                room_id = payload.get('room')
                room = rooms.get(room_id)
                if not room:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room not found'}})
                    continue
                ok = room.add_player(player_id or str(addr[1]), conn)
                if not ok:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room full'}})
                    continue
                current_room = room
                # thông báo cho cả phòng
                broadcast_room(room, {'type': 'ROOM_JOINED', 'payload': {'room': room_id, 'players': list(room.players.keys())}})
                # cập nhật số người chơi phòng cho tất cả
                broadcast_all({'type': 'LIST_ROOMS_RESPONSE', 'payload': {'rooms': build_rooms_list()}})

            elif mtype == 'LIST_ROOMS':
                # Trả về danh sách phòng hiện có với số lượng người chơi
                res = []
                for rid, r in rooms.items():
                    res.append({'room': rid, 'players': len(r.players), 'creator': r.creator})
                send_msg(conn, {'type': 'LIST_ROOMS_RESPONSE', 'payload': {'rooms': res}})

            elif mtype == 'DELETE_ROOM':
                room_id = payload.get('room')
                room = rooms.get(room_id)
                if not room:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room not found'}})
                    continue
                if not room.is_empty():
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room not empty'}})
                    continue
                # chỉ xoá nếu rỗng
                del rooms[room_id]
                send_msg(conn, {'type': 'ROOM_DELETED', 'payload': {'room': room_id}})
                # cập nhật danh sách phòng
                broadcast_all({'type': 'LIST_ROOMS_RESPONSE', 'payload': {'rooms': build_rooms_list()}})

            elif mtype == 'RENAME_ROOM':
                room_id = payload.get('room')
                new_name = payload.get('new')
                room = rooms.get(room_id)
                if not room:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room not found'}})
                    continue
                if not room.is_empty():
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room must be empty to rename'}})
                    continue
                if not new_name:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Missing new name'}})
                    continue
                if new_name in rooms:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Target name exists'}})
                    continue
                # thực hiện đổi tên
                rooms[new_name] = rooms.pop(room_id)
                rooms[new_name].room_id = new_name
                send_msg(conn, {'type': 'ROOM_RENAMED', 'payload': {'old': room_id, 'new': new_name}})
                broadcast_all({'type': 'LIST_ROOMS_RESPONSE', 'payload': {'rooms': build_rooms_list()}})

            # THÊM XỬ LÝ READY VÀ NOT_READY
            elif mtype == 'READY':
                if current_room is None:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Not in room'}})
                    continue
                room_id = payload.get('room')
                if room_id != current_room.room_id:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room mismatch'}})
                    continue
                
                # Đánh dấu player là ready
                current_room.set_player_ready(player_id, True)
                # Broadcast trạng thái ready cho tất cả trong phòng
                broadcast_room(current_room, {
                    'type': 'PLAYER_READY', 
                    'payload': {
                        'player': player_id, 
                        'ready': True,
                        'players_ready': current_room.players_ready
                    }
                })
                
                # Kiểm tra nếu cả 2 đều ready thì tự động bắt đầu game
                if current_room.all_players_ready() and len(current_room.players) == 2:
                    # Reset game state và bắt đầu game mới
                    current_room.reset_game()
                    broadcast_room(current_room, {
                        'type': 'GAME_START', 
                        'payload': {}
                    })
                    # Gửi trạng thái game mới
                    broadcast_room(current_room, {
                        'type': 'GAME_STATE', 
                        'payload': {
                            'board': current_room.game.board, 
                            'turn': current_room.game.turn, 
                            'winner': current_room.game.winner
                        }
                    })

            elif mtype == 'NOT_READY':
                if current_room is None:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Not in room'}})
                    continue
                room_id = payload.get('room')
                if room_id != current_room.room_id:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Room mismatch'}})
                    continue
                
                # Đánh dấu player là not ready
                current_room.set_player_ready(player_id, False)
                # Broadcast trạng thái not ready cho tất cả trong phòng
                broadcast_room(current_room, {
                    'type': 'PLAYER_READY', 
                    'payload': {
                        'player': player_id, 
                        'ready': False,
                        'players_ready': current_room.players_ready
                    }
                })

            elif mtype == 'START_GAME':
                if current_room is None:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Not in room'}})
                    continue
                # Chỉ bắt đầu game nếu có đủ 2 người chơi
                if len(current_room.players) < 2:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Need 2 players to start'}})
                    continue
                
                # Reset game state và bắt đầu game mới
                current_room.reset_game()
                broadcast_room(current_room, {
                    'type': 'GAME_START', 
                    'payload': {}
                })
                # Gửi trạng thái game mới
                broadcast_room(current_room, {
                    'type': 'GAME_STATE', 
                    'payload': {
                        'board': current_room.game.board, 
                        'turn': current_room.game.turn, 
                        'winner': current_room.game.winner
                    }
                })

            elif mtype == 'MOVE':
                if current_room is None:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Not in room'}})
                    continue
                x = payload.get('x')
                y = payload.get('y')
                if x is None or y is None:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Missing coords'}})
                    continue
                # tìm player index: map first player -> 1, second -> 2
                players_list = list(current_room.players.keys())
                try:
                    player_index = players_list.index(player_id) + 1
                except ValueError:
                    # nếu player_id không có (ví dụ không gửi player_id), thử dùng socket order
                    player_index = 1 if conn == list(current_room.players.values())[0] else 2

                # set turn according to GameState
                gs = current_room.game
                if gs.turn != player_index:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Not your turn'}})
                    continue

                ok = gs.make_move(x, y)
                if not ok:
                    send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Invalid move'}})
                    continue

                # broadcast update bàn cờ
                broadcast_room(current_room, {
                    'type': 'GAME_STATE', 
                    'payload': {
                        'board': gs.board, 
                        'turn': gs.turn, 
                        'winner': gs.winner
                    }
                })

            elif mtype == 'CHAT':
                if current_room:
                    broadcast_room(current_room, {
                        'type': 'CHAT', 
                        'payload': {
                            'from': player_id, 
                            'text': payload.get('text')
                        }
                    })

            elif mtype == 'LEAVE':
                # Cho phép LEAVE idempotent: trả về OK ngay cả khi không ở phòng
                if current_room:
                    # Reset trạng thái ready khi rời phòng
                    current_room.set_player_ready(player_id, False)
                    current_room.remove_player(player_id)
                    broadcast_room(current_room, {
                        'type': 'PLAYER_LEFT', 
                        'payload': {
                            'player': player_id
                        }
                    })
                    # Broadcast trạng thái ready cập nhật
                    broadcast_room(current_room, {
                        'type': 'PLAYER_READY', 
                        'payload': {
                            'players_ready': current_room.players_ready
                        }
                    })
                    current_room = None
                    # cập nhật số người chơi
                    broadcast_all({'type': 'LIST_ROOMS_RESPONSE', 'payload': {'rooms': build_rooms_list()}})
                # xác nhận tới client đã xử lý LEAVE
                send_msg(conn, {'type': 'LEFT', 'payload': {}})

            else:
                send_msg(conn, {'type': 'ERROR', 'payload': {'msg': 'Unknown type'}})

    except Exception:
        print('Lỗi xử lý client:')
        traceback.print_exc()
    finally:
        try:
            conn.close()
        except Exception:
            pass
        # nếu ở trong phòng, remove
        if current_room and player_id:
            # Reset trạng thái ready khi disconnect
            current_room.set_player_ready(player_id, False)
            current_room.remove_player(player_id)
            try:
                broadcast_room(current_room, {
                    'type': 'PLAYER_LEFT', 
                    'payload': {
                        'player': player_id
                    }
                })
                # Broadcast trạng thái ready cập nhật
                broadcast_room(current_room, {
                    'type': 'PLAYER_READY', 
                    'payload': {
                        'players_ready': current_room.players_ready
                    }
                })
                broadcast_all({'type': 'LIST_ROOMS_RESPONSE', 'payload': {'rooms': build_rooms_list()}})
            except Exception:
                pass
        # loại bỏ khỏi danh sách client toàn cục
        try:
            clients.remove(conn)
        except Exception:
            pass


def main():
    print(f"Khởi chạy server trên {HOST}:{PORT}")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(100)
    try:
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print('Server đóng')
    finally:
        srv.close()


if __name__ == '__main__':
    main()