"""
Room và GameState cho server.
"""
from typing import Dict
import socket

class GameState:
    def __init__(self):
        self.size = 15
        self.board = [[0] * self.size for _ in range(self.size)]
        self.turn = 1  # 1 hoặc 2
        self.winner = None  # None, 1, hoặc 2

    def make_move(self, x: int, y: int) -> bool:
        """Đặt quân cờ tại (x,y). Trả về True nếu hợp lệ."""
        if self.winner is not None:
            return False
        if not (0 <= x < self.size and 0 <= y < self.size):
            return False
        if self.board[y][x] != 0:
            return False
        
        self.board[y][x] = self.turn
        
        # Kiểm tra chiến thắng
        if self.check_win(x, y):
            self.winner = self.turn
        else:
            # Chuyển lượt
            self.turn = 3 - self.turn  # 1->2, 2->1
            
        return True

    def check_win(self, x: int, y: int) -> bool:
        """Kiểm tra xem nước đi tại (x,y) có chiến thắng không."""
        player = self.board[y][x]
        directions = [
            [(1, 0), (-1, 0)],   # ngang
            [(0, 1), (0, -1)],   # dọc
            [(1, 1), (-1, -1)],  # chéo chính
            [(1, -1), (-1, 1)]   # chéo phụ
        ]
        
        for dir_pair in directions:
            total = 1  # bản thân ô vừa đặt
            for dx, dy in dir_pair:
                nx, ny = x + dx, y + dy
                while 0 <= nx < self.size and 0 <= ny < self.size and self.board[ny][nx] == player:
                    total += 1
                    nx += dx
                    ny += dy
            if total >= 5:
                return True
        return False


class Room:
    def __init__(self, room_id: str, creator: str = ""):
        self.room_id = room_id
        self.players: Dict[str, socket.socket] = {}  # player_id -> socket
        self.players_ready: Dict[str, bool] = {}     # player_id -> ready status
        self.game = GameState()
        self.creator = creator

    def add_player(self, player_id: str, sock: socket.socket) -> bool:
        """Thêm player vào phòng. Trả về False nếu phòng đầy."""
        if len(self.players) >= 2:
            return False
        self.players[player_id] = sock
        self.players_ready[player_id] = False  # Mặc định là chưa sẵn sàng
        return True

    def remove_player(self, player_id: str):
        """Xóa player khỏi phòng."""
        if player_id in self.players:
            del self.players[player_id]
        if player_id in self.players_ready:
            del self.players_ready[player_id]

    def set_player_ready(self, player_id: str, ready: bool):
        """Đặt trạng thái sẵn sàng cho player."""
        if player_id in self.players_ready:
            self.players_ready[player_id] = ready

    def all_players_ready(self) -> bool:
        """Kiểm tra xem tất cả players đã sẵn sàng chưa."""
        if len(self.players) < 2:
            return False
        return all(self.players_ready.values())

    def reset_game(self):
        """Reset game state."""
        self.game = GameState()
        # Có thể reset trạng thái ready nếu muốn
        # for player_id in self.players_ready:
        #     self.players_ready[player_id] = False

    def is_empty(self) -> bool:
        return len(self.players) == 0