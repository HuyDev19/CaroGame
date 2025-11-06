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
        root.title('Caro — Gomoku')
        try:
            # Áp dụng ttk theme cho cảm giác hiện đại hơn
            style = ttk.Style()
            theme = 'clam' if 'clam' in style.theme_names() else style.theme_use()
            style.theme_use(theme)
            style.configure('TButton', padding=6)
            style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
        except Exception:
            pass

        self.player_id = f'P{root.winfo_id()}'

        top = ttk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.X)

        self.connect_btn = ttk.Button(top, text='Kết nối', command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=(6, 0), pady=6)

        self.create_btn = ttk.Button(top, text='Tạo phòng', command=self.create_room)
        self.create_btn.pack(side=tk.LEFT, padx=6, pady=6)

        self.join_btn = ttk.Button(top, text='Tham gia phòng', command=self.join_room)
        self.join_btn.pack(side=tk.LEFT, padx=6, pady=6)

        self.leave_btn = ttk.Button(top, text='Rời phòng', command=self.leave_room)
        self.leave_btn.pack(side=tk.LEFT, padx=6, pady=6)

        # Nút ẩn/hiện bảng phòng
        self.sidebar_visible = True
        self.toggle_side_btn = ttk.Button(top, text='Ẩn phòng', command=self.toggle_sidebar)
        self.toggle_side_btn.pack(side=tk.LEFT, padx=6, pady=6)

        self.status_lbl = ttk.Label(top, text='Chưa kết nối')
        self.status_lbl.pack(side=tk.LEFT, padx=10)

        # Khu vực nội dung chính: Panedwindow để kéo thay đổi kích thước sidebar
        self.pw = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
        self.pw.pack(fill=tk.BOTH, expand=True)
        self.left_pane = ttk.Frame(self.pw)
        self.pw.add(self.left_pane, weight=3)

        # Sidebar hiển thị danh sách phòng
        side = ttk.Frame(self.pw, width=260)
        self.pw.add(side, weight=1)
        ttk.Label(side, text='Phòng hiện có', style='Header.TLabel').pack()
    # Treeview với cột: Phòng, Người, Người tạo
        self.room_tree = ttk.Treeview(side, columns=('room', 'players', 'creator'), show='headings', height=20)
        self.room_tree.heading('room', text='Phòng')
        self.room_tree.heading('players', text='Người')
        self.room_tree.heading('creator', text='Người tạo')
        self.room_tree.column('room', width=160, anchor='w')
        self.room_tree.column('players', width=50, anchor='center')
        self.room_tree.column('creator', width=100, anchor='w')
        self.room_tree.pack(side=tk.LEFT, fill=tk.Y)
        rb_scroll = ttk.Scrollbar(side, orient=tk.VERTICAL, command=self.room_tree.yview)
        rb_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.room_tree.config(yscrollcommand=rb_scroll.set)
    # double-click để tham gia
        self.room_tree.bind('<Double-1>', lambda e: self.join_selected_room())
    # menu chuột phải (context menu)
        self.room_menu = tk.Menu(root, tearoff=0)
        self.room_menu.add_command(label='Tham gia', command=self.join_selected_room)
        self.room_menu.add_command(label='Đổi tên', command=self.rename_selected_room)
        self.room_menu.add_command(label='Xóa', command=self.delete_selected_room)
        self.room_tree.bind('<Button-3>', self._on_room_right_click)
    # hiển thị số phòng
        self.room_count_lbl = ttk.Label(side, text='0 phòng')
        self.room_count_lbl.pack(pady=(6,0))

        btn_frame = ttk.Frame(side)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text='Làm mới', command=lambda: self.refresh_rooms()).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text='Tham gia', command=lambda: self.join_selected_room()).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text='Đổi tên', command=lambda: self.rename_selected_room()).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text='Xóa', command=lambda: self.delete_selected_room()).pack(fill=tk.X, pady=2)

        # canvas bàn cờ
        self.size = 15
        self.cell = 40
        # Canvas kích thước chính xác theo số ô; mỗi ô là một ô vuông
        board_bg = '#f5deb3'  # wheat
        self.board_bg = board_bg
        self.grid_color = '#b29762'
        self.canvas = tk.Canvas(self.left_pane, width=self.size*self.cell, height=self.size*self.cell, bg=board_bg, highlightthickness=0)
        # Canvas chiếm toàn bộ khu vực trái
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.canvas.bind('<Button-1>', self.on_click)
        # Lắng nghe thay đổi kích thước để scale theo tỉ lệ
        self.canvas.bind('<Configure>', self._on_canvas_resize)

        # queue để nhận message từ thread mạng
        self.q = queue.Queue()

        self.conn = None
        # cached rooms list as provided by server: list of dicts {room, players}
        self._rooms = []
        # board[y][x]
        self.board = [[0]*self.size for _ in range(self.size)]
        # flag to disable input during animations
        self._animating = False

        # vẽ lưới lần đầu
        self._draw_grid()

        # thanh trạng thái/hướng dẫn cuối cửa sổ
        try:
            bottom = ttk.Frame(root)
            bottom.pack(side=tk.BOTTOM, fill=tk.X)
            self.hint_lbl = ttk.Label(bottom, text='Gợi ý: Nhấp vào bàn cờ để đánh; tạo phòng để chơi với người khác.')
            self.hint_lbl.pack(side=tk.LEFT, padx=8, pady=6)
        except Exception:
            pass

        # kiểm tra queue theo chu kỳ
        self.root.after(100, self._process_queue)

        # Lưu tham chiếu để toggle và nhớ bề rộng gần nhất
        self.side_frame = side
        self.sidebar_width = 260

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
        if self._animating:
            # ignore clicks while win animation is running
            return
        if not self.conn:
            return
        # Tính ô dựa trên vị trí click với phần bù căn giữa (offset)
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        grid_pix = self.size * self.cell
        ox = max((cw - grid_pix) // 2, 0)
        oy = max((ch - grid_pix) // 2, 0)
        gx = event.x - ox
        gy = event.y - oy
        if gx < 0 or gy < 0:
            return
        x = gx // self.cell
        y = gy // self.cell
        if 0 <= x < self.size and 0 <= y < self.size:
            self.conn.send('MOVE', {'x': int(x), 'y': int(y)})

    def _process_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()
                self._handle_msg(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def toggle_sidebar(self):
        if self.sidebar_visible:
            # Ghi nhớ bề rộng hiện tại của sidebar trước khi ẩn
            try:
                w = self.side_frame.winfo_width()
                if w > 50:
                    self.sidebar_width = w
            except Exception:
                pass
            try:
                self.pw.forget(self.side_frame)
            except Exception:
                pass
            self.sidebar_visible = False
            try:
                self.toggle_side_btn.config(text='Hiện phòng')
            except Exception:
                pass
        else:
            try:
                self.pw.add(self.side_frame, weight=1)
                self.root.update_idletasks()
                # Đặt vị trí sash để khôi phục bề rộng sidebar (nếu API hỗ trợ)
                try:
                    pw_w = max(self.pw.winfo_width(), 1)
                    newpos = max(100, pw_w - int(self.sidebar_width))
                    self.pw.sashpos(0, newpos)
                except Exception:
                    pass
            except Exception:
                pass
            self.sidebar_visible = True
            try:
                self.toggle_side_btn.config(text='Ẩn phòng')
            except Exception:
                pass

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
            # lưu cache danh sách phòng để hỗ trợ tên có dấu/khoảng trắng/unicode
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
                # attempt to find the winning line locally and animate it
                win_coords = self.find_winning_line(self.board, win_len=5)
                if win_coords:
                    # animate then show message
                    def after_anim():
                        messagebox.showinfo('Kết thúc', f"Người thắng: {payload.get('winner')}")
                    self.animate_win(win_coords, callback=after_anim)
                else:
                    # fallback: just show message
                    messagebox.showinfo('Kết thúc', f"Người thắng: {payload.get('winner')}")
        elif mtype == 'CHAT':
            # chat hiện chưa hiển thị, có thể mở rộng
            print('CHAT', payload)

    def _draw_board(self):
        # Xóa các quân cờ cũ
        self.canvas.delete('stone')

        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        grid_pix = self.size * self.cell
        ox = max((cw - grid_pix) // 2, 0)
        oy = max((ch - grid_pix) // 2, 0)

        pad = int(self.cell * 0.18)
        for y in range(self.size):
            for x in range(self.size):
                v = self.board[y][x]
                if v != 0:
                    x1 = ox + x * self.cell + pad
                    y1 = oy + y * self.cell + pad
                    x2 = x1 + (self.cell - 2*pad)
                    y2 = y1 + (self.cell - 2*pad)
                    if v == 1:
                        fill = '#222222'  # đen
                        outline = '#111111'
                    else:
                        fill = '#f7f7f7'  # trắng
                        outline = '#d0d0d0'
                    self.canvas.create_oval(x1, y1, x2, y2, fill=fill, outline=outline, width=2, tags='stone')

    def _draw_grid(self):
        # Vẽ lại lưới theo kích thước hiện tại và căn giữa
        self.canvas.delete('cell')
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        cell = self.cell
        grid_pix = self.size * cell
        ox = max((cw - grid_pix) // 2, 0)
        oy = max((ch - grid_pix) // 2, 0)
        for y in range(self.size):
            for x in range(self.size):
                x1 = ox + x * cell
                y1 = oy + y * cell
                x2 = x1 + cell
                y2 = y1 + cell
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline=self.grid_color,
                    fill=self.board_bg,
                    tags=('cell', f'cell_{x}_{y}')
                )

    def _on_canvas_resize(self, event):
        try:
            # Tính kích thước ô mới theo cạnh ngắn hơn để giữ tỉ lệ vuông
            new_cell = max(16, int(min(event.width, event.height) / max(self.size, 1)))
        except Exception:
            new_cell = self.cell
        if new_cell != self.cell:
            self.cell = new_cell
        # Luôn vẽ lại để căn giữa chính xác
        self._draw_grid()
        self._draw_board()

    def find_winning_line(self, board, win_len=5):
        """Tìm và trả về danh sách (x,y) của đường thắng nếu có, ngược lại trả về [].
        `board` là danh sách các hàng: board[y][x]
        """
        H = len(board)
        W = len(board[0]) if H>0 else 0
        dirs = [(1,0),(0,1),(1,1),(1,-1)]
        for y in range(H):
            for x in range(W):
                v = board[y][x]
                if v == 0:
                    continue
                for dx,dy in dirs:
                    coords = [(x,y)]
                    nx, ny = x+dx, y+dy
                    while 0 <= nx < W and 0 <= ny < H and board[ny][nx] == v:
                        coords.append((nx, ny))
                        nx += dx
                        ny += dy
                    # kiểm tra thêm hướng ngược lại để thu được toàn bộ đoạn thẳng
                    bx, by = x-dx, y-dy
                    while 0 <= bx < W and 0 <= by < H and board[by][bx] == v:
                        coords.insert(0, (bx, by))
                        bx -= dx
                        by -= dy
                    if len(coords) >= win_len:
                        return coords
        return []

    def animate_win(self, coords, callback=None, cycles=6, interval=250):
        """Hiệu ứng nhấp nháy (blink) tô sáng các ô trong `coords` (danh sách (x,y)).
        Sau khi animation kết thúc sẽ gọi `callback()` nếu có.
        """
        if not coords:
            if callback:
                callback()
            return
        self._animating = True
        orig_fills = {}
        highlight = 'gold'

    # lưu màu fill ban đầu của từng ô để phục hồi sau animation
        for x,y in coords:
            tag = f'cell_{x}_{y}'
            items = self.canvas.find_withtag(tag)
            for it in items:
                try:
                    orig = self.canvas.itemcget(it, 'fill')
                except Exception:
                    orig = ''
                orig_fills[it] = orig

        step = {'i': 0}

        def pulse():
            i = step['i']
        # bật/tắt màu highlight (toggle)
            make_high = (i % 2 == 0)
            for it, orig in orig_fills.items():
                try:
                    self.canvas.itemconfigure(it, fill=(highlight if make_high else orig))
                except Exception:
                    pass
            step['i'] += 1
            if step['i'] <= cycles:
                self.root.after(interval, pulse)
            else:
                # đảm bảo phục hồi màu fill ban đầu
                for it, orig in orig_fills.items():
                    try:
                        self.canvas.itemconfigure(it, fill=orig)
                    except Exception:
                        pass
                self._animating = False
                if callback:
                    try:
                        callback()
                    except Exception:
                        pass

        pulse()


if __name__ == '__main__':
    root = tk.Tk()
    app = CaroGUI(root)
    root.mainloop()
