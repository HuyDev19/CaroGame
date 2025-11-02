"""
Client GUI bằng tkinter.
Giao diện đơn giản: kết nối server, tạo/tham gia phòng, bàn cờ 15x15, click để gửi MOVE.
Chú thích bằng tiếng Việt.
"""
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
import queue
import os
import sys

# Đảm bảo project root có trong sys.path để Python tìm package `common` khi
# chạy file GUI trực tiếp: `python client/gui.py`.
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from client.client import ClientConnection

HOST = '127.0.0.1'
PORT = 5000


class CaroGUI:
    def __init__(self, root):
        self.root = root
        root.title('Caro Client')

        self.player_id = f'P{root.winfo_id()}'

        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.X)

        self.connect_btn = tk.Button(top, text='Kết nối', command=self.connect)
        self.connect_btn.pack(side=tk.LEFT)

        self.create_btn = tk.Button(top, text='Tạo phòng', command=self.create_room)
        self.create_btn.pack(side=tk.LEFT)

        self.join_btn = tk.Button(top, text='Tham gia phòng', command=self.join_room)
        self.join_btn.pack(side=tk.LEFT)

        self.leave_btn = tk.Button(top, text='Rời phòng', command=self.leave_room)
        self.leave_btn.pack(side=tk.LEFT)

        self.status_lbl = tk.Label(top, text='Chưa kết nối')
        self.status_lbl.pack(side=tk.LEFT, padx=10)

        # Sidebar hiển thị danh sách phòng
        side = tk.Frame(root)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        tk.Label(side, text='Phòng hiện có').pack()
        # Treeview with columns: Room, Players, Creator
        self.room_tree = ttk.Treeview(side, columns=('room', 'players', 'creator'), show='headings', height=20)
        self.room_tree.heading('room', text='Phòng')
        self.room_tree.heading('players', text='Người')
        self.room_tree.heading('creator', text='Người tạo')
        self.room_tree.column('room', width=160, anchor='w')
        self.room_tree.column('players', width=50, anchor='center')
        self.room_tree.column('creator', width=100, anchor='w')
        self.room_tree.pack(side=tk.LEFT, fill=tk.Y)
        rb_scroll = tk.Scrollbar(side, orient=tk.VERTICAL, command=self.room_tree.yview)
        rb_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.room_tree.config(yscrollcommand=rb_scroll.set)
        # double-click to join
        self.room_tree.bind('<Double-1>', lambda e: self.join_selected_room())
        # right-click context menu
        self.room_menu = tk.Menu(root, tearoff=0)
        self.room_menu.add_command(label='Tham gia', command=self.join_selected_room)
        self.room_menu.add_command(label='Đổi tên', command=self.rename_selected_room)
        self.room_menu.add_command(label='Xóa', command=self.delete_selected_room)
        self.room_tree.bind('<Button-3>', self._on_room_right_click)
        # room count
        self.room_count_lbl = tk.Label(side, text='0 phòng')
        self.room_count_lbl.pack(pady=(6,0))

        btn_frame = tk.Frame(side)
        btn_frame.pack(fill=tk.X, pady=4)
        tk.Button(btn_frame, text='Làm mới', command=lambda: self.refresh_rooms()).pack(fill=tk.X)
        tk.Button(btn_frame, text='Tham gia', command=lambda: self.join_selected_room()).pack(fill=tk.X)
        tk.Button(btn_frame, text='Đổi tên', command=lambda: self.rename_selected_room()).pack(fill=tk.X)
        tk.Button(btn_frame, text='Xóa', command=lambda: self.delete_selected_room()).pack(fill=tk.X)

        # canvas bàn cờ
        self.size = 15
        self.cell = 40
        # Canvas kích thước chính xác theo số ô; mỗi ô là một ô vuông
        self.canvas = tk.Canvas(root, width=self.size*self.cell, height=self.size*self.cell, bg='white')
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.on_click)

        # queue để nhận message từ thread mạng
        self.q = queue.Queue()

        self.conn = None
        # cached rooms list as provided by server: list of dicts {room, players}
        self._rooms = []
        # board[y][x]
        self.board = [[0]*self.size for _ in range(self.size)]

        # vẽ lưới bằng rectangles (ô vuông) — mỗi ô có tag 'cell'
        for y in range(self.size):
            for x in range(self.size):
                x1 = x * self.cell
                y1 = y * self.cell
                x2 = x1 + self.cell
                y2 = y1 + self.cell
                self.canvas.create_rectangle(x1, y1, x2, y2, outline='black', fill='lightgray', tags=('cell', f'cell_{x}_{y}'))

        # kiểm tra queue theo chu kỳ
        self.root.after(100, self._process_queue)

    def connect(self):
        if self.conn:
            messagebox.showinfo('Info', 'Đã kết nối')
            return
        try:
            self.conn = ClientConnection(HOST, PORT, self.player_id, lambda m: self.q.put(m))
            self.conn.connect()
            self.status_lbl.config(text='Đã kết nối')
            # tự động load danh sách phòng sau khi kết nối
            self.refresh_rooms()
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không kết nối: {e}')

    def create_room(self):
        if not self.conn:
            messagebox.showwarning('Chưa kết nối', 'Vui lòng kết nối trước')
            return
        room = simpledialog.askstring('Tạo phòng', 'Tên phòng:')
        if room:
            try:
                self.conn.send('CREATE_ROOM', {'room': room})
            except Exception as e:
                # Hiển thị lỗi (nếu kết nối bị reset)
                messagebox.showerror('Lỗi kết nối', f"Gửi CREATE_ROOM thất bại: {e}")

    def join_room(self):
        if not self.conn:
            messagebox.showwarning('Chưa kết nối', 'Vui lòng kết nối trước')
            return
        room = simpledialog.askstring('Tham gia phòng', 'Tên phòng:')
        if room:
            self.conn.send('JOIN_ROOM', {'room': room})
            # refresh list after join (server will also broadcast ROOM_JOINED)
            self.refresh_rooms()

    def join_selected_room(self):
        sel = self.room_tree.selection()
        if not sel:
            messagebox.showwarning('Chọn phòng', 'Vui lòng chọn phòng để tham gia')
            return
        item = sel[0]
        idx = self.room_tree.index(item)
        if idx < 0 or idx >= len(self._rooms):
            messagebox.showerror('Lỗi', 'Chỉ số phòng không hợp lệ')
            return
        room = self._rooms[idx].get('room')
        self.conn.send('JOIN_ROOM', {'room': room})
        self.refresh_rooms()

    def leave_room(self):
        """Gửi lệnh LEAVE tới server (rời phòng hiện tại)."""
        if not self.conn:
            return
        try:
            self.conn.send('LEAVE', {})
            # cập nhật UI: xoá bàn cờ và label
            self.board = [[0]*self.size for _ in range(self.size)]
            self._draw_board()
            self.status_lbl.config(text='Đã rời phòng')
            self.refresh_rooms()
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể rời phòng: {e}')

    def refresh_rooms(self):
        if not self.conn:
            return
        try:
            self.conn.send('LIST_ROOMS', {})
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể lấy danh sách phòng: {e}')

    def delete_selected_room(self):
        sel = self.room_tree.selection()
        if not sel:
            messagebox.showwarning('Chọn phòng', 'Vui lòng chọn phòng để xóa')
            return
        item = sel[0]
        idx = self.room_tree.index(item)
        if idx < 0 or idx >= len(self._rooms):
            messagebox.showerror('Lỗi', 'Chỉ số phòng không hợp lệ')
            return
        room = self._rooms[idx].get('room')
        if messagebox.askyesno('Xác nhận', f'Bạn có chắc muốn xóa phòng {room}? (phòng phải rỗng)'):
            try:
                self.conn.send('DELETE_ROOM', {'room': room})
            except Exception as e:
                messagebox.showerror('Lỗi', f'Xóa phòng thất bại: {e}')

    def rename_selected_room(self):
        sel = self.room_tree.selection()
        if not sel:
            messagebox.showwarning('Chọn phòng', 'Vui lòng chọn phòng để đổi tên')
            return
        item = sel[0]
        idx = self.room_tree.index(item)
        if idx < 0 or idx >= len(self._rooms):
            messagebox.showerror('Lỗi', 'Chỉ số phòng không hợp lệ')
            return
        room = self._rooms[idx].get('room')
        new = simpledialog.askstring('Đổi tên phòng', f'Tên mới cho {room}:')
        if new:
            try:
                self.conn.send('RENAME_ROOM', {'room': room, 'new': new})
            except Exception as e:
                messagebox.showerror('Lỗi', f'Đổi tên thất bại: {e}')

    def on_click(self, event):
        if not self.conn:
            return
        # Tính ô dựa trên vị trí click (mỗi ô có kích thước self.cell)
        x = event.x // self.cell
        y = event.y // self.cell
        if 0 <= x < self.size and 0 <= y < self.size:
            self.conn.send('MOVE', {'x': x, 'y': y})

    def _process_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()
                self._handle_msg(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def _on_room_right_click(self, event):
        # Select the row under cursor and popup context menu
        try:
            item = self.room_tree.identify_row(event.y)
            if item:
                self.room_tree.selection_set(item)
                # popup menu
                self.room_menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self.room_menu.grab_release()
            except Exception:
                pass

    def _handle_msg(self, msg: dict):
        mtype = msg.get('type')
        payload = msg.get('payload', {})
        if mtype == 'ERROR':
            messagebox.showerror('Server lỗi', payload.get('msg'))
        elif mtype == 'ROOM_CREATED':
            messagebox.showinfo('OK', f"Đã tạo phòng {payload.get('room')}")
        elif mtype == 'LIST_ROOMS_RESPONSE':
            # payload.rooms = [{room, players, creator?}, ...]
            rooms = payload.get('rooms', [])
            # cache rooms so we can support names with spaces/unicode
            self._rooms = rooms
            # refresh tree
            for iid in self.room_tree.get_children():
                self.room_tree.delete(iid)
            for r in rooms:
                name = r.get('room')
                players = r.get('players')
                creator = r.get('creator', '')
                # insert row; Treeview will keep insertion order so index mapping works
                self.room_tree.insert('', tk.END, values=(name, players, creator))
            # update count label
            try:
                self.room_count_lbl.config(text=f"{len(rooms)} phòng")
            except Exception:
                pass
        elif mtype == 'ROOM_DELETED':
            room = payload.get('room')
            messagebox.showinfo('OK', f"Đã xóa phòng {room}")
            self.refresh_rooms()
        elif mtype == 'ROOM_RENAMED':
            old = payload.get('old')
            new = payload.get('new')
            messagebox.showinfo('OK', f"Đổi tên phòng {old} -> {new}")
            self.refresh_rooms()
        elif mtype == 'ROOM_JOINED':
            players = payload.get('players')
            self.status_lbl.config(text=f'Trong phòng: {players}')
        elif mtype == 'GAME_STATE':
            board = payload.get('board')
            self.board = board
            self._draw_board()
            if payload.get('winner'):
                messagebox.showinfo('Kết thúc', f"Người thắng: {payload.get('winner')}")
        elif mtype == 'CHAT':
            # chat hiện chưa hiển thị, có thể mở rộng
            print('CHAT', payload)

    def _draw_board(self):
        # Xóa các text quân cờ cũ
        self.canvas.delete('stone')
        # Dùng font lớn cho X/O
        try:
            font = ('Arial', int(self.cell*0.5), 'bold')
        except Exception:
            font = None

        for y in range(self.size):
            for x in range(self.size):
                v = self.board[y][x]
                if v != 0:
                    cx = x*self.cell + self.cell/2
                    cy = y*self.cell + self.cell/2
                    symbol = 'X' if v == 1 else 'O'
                    color = 'black' if v == 1 else 'red'
                    # vẽ ký tự ở giữa ô
                    self.canvas.create_text(cx, cy, text=symbol, fill=color, font=font, tags='stone')


if __name__ == '__main__':
    root = tk.Tk()
    app = CaroGUI(root)
    root.mainloop()
