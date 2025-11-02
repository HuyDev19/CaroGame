"""
Logic trò chơi Caro và lớp Room để quản lý ván.
Chú thích bằng tiếng Việt.
"""
from typing import List, Optional, Tuple


class GameState:
    """Quản lý trạng thái bàn cờ và kiểm tra thắng."""

    def __init__(self, size: int = 15, win_len: int = 5):
        self.size = size
        self.win_len = win_len
        # board[y][x]: 0-empty, 1-player1 (X), 2-player2 (O)
        self.board: List[List[int]] = [[0] * size for _ in range(size)]
        self.turn = 1  # 1 hoặc 2
        self.winner: Optional[int] = None

    def make_move(self, x: int, y: int) -> bool:
        """Cố gắng đặt nước đi. Trả về True nếu hợp lệ và được đặt.
        Ghi chú: chỉ gọi khi chưa có người thắng.
        """
        if self.winner is not None:
            return False
        if not (0 <= x < self.size and 0 <= y < self.size):
            return False
        if self.board[y][x] != 0:
            return False
        self.board[y][x] = self.turn
        if self.check_win(x, y):
            self.winner = self.turn
        else:
            # chuyển lượt
            self.turn = 1 if self.turn == 2 else 2
        return True

    def check_win(self, x: int, y: int) -> bool:
        """Kiểm tra xem nước đi (x,y) của người `self.board[y][x]` có thắng không.
        Kiểm tra 4 hướng: ngang, dọc, chéo xuống phải, chéo xuống trái.
        """
        player = self.board[y][x]
        if player == 0:
            return False

        directions: List[Tuple[int, int]] = [
            (1, 0),  # ngang
            (0, 1),  # dọc
            (1, 1),  # chéo ↘
            (1, -1),  # chéo ↗
        ]

        for dx, dy in directions:
            count = 1
            # đi về phía dương
            nx, ny = x + dx, y + dy
            while 0 <= nx < self.size and 0 <= ny < self.size and self.board[ny][nx] == player:
                count += 1
                nx += dx
                ny += dy
            # đi về phía âm
            nx, ny = x - dx, y - dy
            while 0 <= nx < self.size and 0 <= ny < self.size and self.board[ny][nx] == player:
                count += 1
                nx -= dx
                ny -= dy

            if count >= self.win_len:
                return True
        return False

    def is_full(self) -> bool:
        return all(cell != 0 for row in self.board for cell in row)


class Room:
    """Lớp Room quản lý hai người chơi và GameState."""

    def __init__(self, room_id: str, size: int = 15, creator: str = None):
        self.room_id = room_id
        self.players = {}  # player_id -> socket-like object (server giữ tham chiếu)
        self.game = GameState(size=size)
        # người tạo phòng (player_id) nếu có — để phân quyền xoá/rename nếu cần
        self.creator = creator

    def is_empty(self) -> bool:
        return len(self.players) == 0

    def add_player(self, player_id: str, sock) -> bool:
        if len(self.players) >= 2:
            return False
        self.players[player_id] = sock
        return True

    def remove_player(self, player_id: str) -> None:
        if player_id in self.players:
            del self.players[player_id]
