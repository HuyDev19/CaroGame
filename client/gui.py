"""
Client GUI bằng tkinter.
Giao diện đơn giản: kết nối server, tạo/tham gia phòng, bàn cờ 15x15, click để gửi MOVE.
Chú thích bằng tiếng Việt.
"""
import winsound
import os
CLICK_SOUND = os.path.join(os.path.dirname(__file__), "sounds", "click.wav")
WIN_SOUND = os.path.join(os.path.dirname(__file__), "sounds", "win.wav")
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
        root.configure(bg='#2c3e50')
        
        # Cấu hình style hiện đại
        self.setup_styles()
        
        # Phím tắt: Ctrl+R refresh, Ctrl+J join, Ctrl+B toggle sidebar
        root.bind('<Control-r>', lambda e: self.refresh_rooms())
        root.bind('<Control-R>', lambda e: self.refresh_rooms())
        root.bind('<Control-j>', lambda e: self.join_selected_room())
        root.bind('<Control-J>', lambda e: self.join_selected_room())
        root.bind('<Control-b>', lambda e: self.toggle_sidebar())
        root.bind('<Control-B>', lambda e: self.toggle_sidebar())

        # Bắt sự kiện đóng cửa sổ để gửi LEAVE và ngắt kết nối đúng cách
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.player_id = f'P{root.winfo_id()}'
        self.current_room = None
        self.ready_status = False
        self.players_ready = {}  # Dictionary để theo dõi trạng thái sẵn sàng của người chơi
        self.game_started = False  # Trạng thái game đã bắt đầu chưa
        self.game_ended = False  # Trạng thái game kết thúc
        self.sidebar_visible = True  # Trạng thái hiển thị của sidebar

        # Header với gradient
        header = tk.Frame(root, bg='#34495e', height=80)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)
        
        # Tiêu đề game
        title_label = tk.Label(header, text='🎮 CARO VIỆT NAM', font=('Segoe UI', 20, 'bold'), 
                              fg='white', bg='#34495e')
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Frame chứa các nút điều khiển
        control_frame = tk.Frame(header, bg='#34495e')
        control_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Các nút điều khiển
        self.connect_btn = ttk.Button(control_frame, text='🔗 Kết nối', command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=3)
        
        self.create_btn = ttk.Button(control_frame, text='➕ Tạo phòng', command=self.create_room, state='disabled')
        self.create_btn.pack(side=tk.LEFT, padx=3)
        
        self.join_btn = ttk.Button(control_frame, text='🚪 Tham gia', command=self.join_room, state='disabled')
        self.join_btn.pack(side=tk.LEFT, padx=3)
        
        self.leave_btn = ttk.Button(control_frame, text='👋 Rời phòng', command=self.leave_room, state='disabled')
        self.leave_btn.pack(side=tk.LEFT, padx=3)

        self.ready_btn = ttk.Button(control_frame, text='⚡ Sẵn sàng', command=self.toggle_ready, state='disabled')
        self.ready_btn.pack(side=tk.LEFT, padx=3)

        # Nút ẩn/hiện sidebar
        self.toggle_sidebar_btn = ttk.Button(control_frame, text='📋', command=self.toggle_sidebar, width=3)
        self.toggle_sidebar_btn.pack(side=tk.LEFT, padx=3)

        # Main content area
        self.main_frame = tk.Frame(root, bg='#ecf0f1')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Bàn cờ và thông tin
        self.left_panel = tk.Frame(self.main_frame, bg='#ecf0f1')
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Status và info panel
        info_frame = tk.Frame(self.left_panel, bg='white', relief='ridge', bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_lbl = tk.Label(info_frame, text='🔴 Chưa kết nối server', font=('Segoe UI', 11), 
                                  fg='#e74c3c', bg='white')
        self.status_lbl.pack(side=tk.LEFT, padx=15, pady=10)

        self.room_info_lbl = tk.Label(info_frame, text='', font=('Segoe UI', 10), 
                                     fg='#7f8c8d', bg='white')
        self.room_info_lbl.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # Bàn cờ container với shadow effect
        board_container = tk.Frame(self.left_panel, bg='#bdc3c7', padx=3, pady=3)
        board_container.pack(expand=True, fill=tk.BOTH)
        
        # Canvas bàn cờ
        self.size = 15
        self.cell = 40
        self.board_bg = '#e8c87e'  # Màu gỗ nhạt
        self.grid_color = '#8b6914'  # Màu nâu đậm
        self.canvas = tk.Canvas(board_container, width=self.size*self.cell, height=self.size*self.cell, 
                               bg=self.board_bg, highlightthickness=0, relief='sunken', bd=3)
        self.canvas.pack(expand=True, padx=2, pady=2)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Configure>', self._on_canvas_resize)

        # Panel thông báo
        self.notification_frame = tk.Frame(self.left_panel, bg='#34495e', height=50)
        self.notification_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.notification_frame.pack_propagate(False)
        
        self.notification_label = tk.Label(self.notification_frame, text='Chào mừng đến với Caro Việt Nam! 🎮', font=('Segoe UI', 10), 
                                         fg='white', bg='#34495e', wraplength=600)
        self.notification_label.pack(expand=True, pady=15)

        # Right panel - Danh sách phòng và trạng thái
        self.right_panel = tk.Frame(self.main_frame, bg='white', width=320, relief='ridge', bd=2)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.right_panel.pack_propagate(False)
        
        # Header danh sách phòng
        room_header = tk.Frame(self.right_panel, bg='#3498db', height=50)
        room_header.pack(fill=tk.X)
        room_header.pack_propagate(False)
        
        room_title = tk.Label(room_header, text='🎯 DANH SÁCH PHÒNG', font=('Segoe UI', 12, 'bold'), 
                            fg='white', bg='#3498db')
        room_title.pack(side=tk.LEFT, padx=15, pady=15)
        
        # Panel trạng thái người chơi trong phòng
        self.players_frame = tk.Frame(self.right_panel, bg='#f8f9fa', height=120)
        self.players_frame.pack(fill=tk.X, padx=10, pady=10)
        self.players_frame.pack_propagate(False)
        
        tk.Label(self.players_frame, text='TRẠNG THÁI NGƯỜI CHƠI', font=('Segoe UI', 10, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(10, 5))
        
        self.player1_status = tk.Label(self.players_frame, text='Người chơi 1: 🔴 Chưa sẵn sàng', 
                                      font=('Segoe UI', 9), bg='#f8f9fa', fg='#e74c3c')
        self.player1_status.pack(anchor='w', padx=10)
        
        self.player2_status = tk.Label(self.players_frame, text='Người chơi 2: 🔴 Chưa sẵn sàng', 
                                      font=('Segoe UI', 9), bg='#f8f9fa', fg='#e74c3c')
        self.player2_status.pack(anchor='w', padx=10, pady=(2, 10))
        
        self.game_status = tk.Label(self.players_frame, text='🟡 Đang chờ người chơi...', 
                                   font=('Segoe UI', 9, 'bold'), bg='#f8f9fa', fg='#f39c12')
        self.game_status.pack(anchor='w', padx=10, pady=(5, 0))
        
        # Controls cho phòng
        room_controls = tk.Frame(self.right_panel, bg='#ecf0f1', pady=10)
        room_controls.pack(fill=tk.X, padx=10)
        
        ttk.Button(room_controls, text='🔄 Làm mới', command=self.refresh_rooms, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(room_controls, text='🎮 Tham gia', command=self.join_selected_room, width=12).pack(side=tk.RIGHT, padx=2)
        
        # Treeview danh sách phòng
        tree_frame = tk.Frame(self.right_panel, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.room_tree = ttk.Treeview(tree_frame, columns=('room', 'players', 'creator'), show='headings', height=12)
        
        # Định dạng cột
        self.room_tree.heading('room', text='TÊN PHÒNG')
        self.room_tree.heading('players', text='👤')
        self.room_tree.heading('creator', text='NGƯỜI TẠO')
        
        self.room_tree.column('room', width=120, anchor='w')
        self.room_tree.column('players', width=50, anchor='center')
        self.room_tree.column('creator', width=120, anchor='w')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.room_tree.yview)
        self.room_tree.configure(yscrollcommand=scrollbar.set)
        
        self.room_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.room_tree.bind('<Double-1>', lambda e: self.join_selected_room())
        
        # Footer với thông tin
        footer = tk.Frame(self.right_panel, bg='#34495e', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        self.room_count_lbl = tk.Label(footer, text='0 phòng', font=('Segoe UI', 9), 
                                      fg='white', bg='#34495e')
        self.room_count_lbl.pack(expand=True)

        # queue để nhận message từ thread mạng
        self.q = queue.Queue()
        self.conn = None
        self._rooms = []
        self.board = [[0]*self.size for _ in range(self.size)]
        self._animating = False

        # Vẽ lưới ban đầu
        self._draw_grid()

        # Kiểm tra queue theo chu kỳ
        self.root.after(100, self._process_queue)

    def toggle_sidebar(self):
        """Ẩn/hiện bảng danh sách phòng"""
        if self.sidebar_visible:
            # Ẩn sidebar
            self.right_panel.pack_forget()
            self.toggle_sidebar_btn.config(text='📋')
            self.sidebar_visible = False
            self.show_notification("Đã ẩn danh sách phòng", "info")
        else:
            # Hiện sidebar
            self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
            self.toggle_sidebar_btn.config(text='📋')
            self.sidebar_visible = True
            self.show_notification("Đã hiện danh sách phòng", "info")

    def setup_styles(self):
        """Cấu hình styles cho giao diện hiện đại"""
        style = ttk.Style()
        
        # Cố gắng sử dụng theme hiện đại
        modern_themes = ['vista', 'xpnative', 'winnative']
        for theme in modern_themes:
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        
        # Configure styles - THAY ĐỔI MÀU Ở ĐÂY
        style.configure('TButton', font=('Segoe UI', 9), padding=6,
                    background='#3498db', foreground='Black',
               relief='raised', borderwidth=5)
        style.configure('Accent.TButton', font=('Segoe UI', 9, 'bold'), 
                    background='#2ecc71', foreground='Black',
               relief='raised', borderwidth=5)
        style.configure('Success.TButton', font=('Segoe UI', 9, 'bold'),
                    background='#e74c3c', foreground='Black',
               relief='raised', borderwidth=5)
        style.configure('Disabled.TButton', font=('Segoe UI', 9),
                    background="#77c284", foreground='Black',
               relief='raised', borderwidth=5)
        style.configure('Connected.TButton', font=('Segoe UI', 9, 'bold'),
                    background='#9b59b6', foreground='Black',
               relief='raised', borderwidth=5)
        style.configure('Treeview', font=('Segoe UI', 9), rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'), 
                    background="#80e1f9")
    
        # Map styles for hover effects - THAY ĐỔI MÀU HOVER Ở ĐÂY
        style.map('Accent.TButton', 
                background=[('active', '#27ae60'), ('pressed', '#229954')])
        style.map('Success.TButton',
                background=[('active', '#c0392b'), ('pressed', '#a93226')])
        style.map('Disabled.TButton',
                background=[('active', '#7f8c8d'), ('pressed', '#95a5a6')])
        style.map('Connected.TButton',
                background=[('active', '#8e44ad'), ('pressed', '#7d3c98')])
        style.map('TButton',
                background=[('active', '#2980b9'), ('pressed', '#2471a3')])

    def toggle_ready(self):
        """Chuyển trạng thái sẵn sàng"""
        if not self.conn or not self.current_room:
            self.show_notification("Bạn chưa tham gia phòng nào!", "warning")
            return
            
        # KHÔNG cho phép thay đổi trạng thái sẵn sàng khi đang trong trận
        if self.game_started and not self.game_ended:
            self.show_notification("Không thể thay đổi trạng thái sẵn sàng khi đang trong trận đấu!", "warning")
            return
            
        self.ready_status = not self.ready_status
        if self.ready_status:
            self.ready_btn.config(style='Success.TButton', text='✅ Đã sẵn sàng')
            self.show_notification("Bạn đã sẵn sàng tham gia trận đấu! 🎯", "success")
            # Gửi trạng thái sẵn sàng tới server
            try:
                self.conn.send('READY', {'room': self.current_room})
                # Cập nhật trạng thái ngay lập tức
                self.update_player_status(self.player_id, True)
            except Exception as e:
                print(f"Lỗi gửi trạng thái sẵn sàng: {e}")
                self.show_notification("Lỗi gửi trạng thái sẵn sàng!", "error")
        else:
            self.ready_btn.config(style='Accent.TButton', text='⚡ Sẵn sàng')
            self.show_notification("Bạn đã hủy trạng thái sẵn sàng", "warning")
            try:
                self.conn.send('NOT_READY', {'room': self.current_room})
                # Cập nhật trạng thái ngay lập tức
                self.update_player_status(self.player_id, False)
            except Exception as e:
                print(f"Lỗi gửi trạng thái chưa sẵn sàng: {e}")
                self.show_notification("Lỗi gửi trạng thái chưa sẵn sàng!", "error")

    def show_notification(self, message, msg_type="info"):
        """Hiển thị thông báo trên thanh thông báo"""
        if msg_type == "info":
            bg_color = "#3498db"
            icon = "ℹ️"
        elif msg_type == "success":
            bg_color = "#27ae60"
            icon = "✅"
        elif msg_type == "warning":
            bg_color = "#f39c12"
            icon = "⚠️"
        else:  # error
            bg_color = "#e74c3c"
            icon = "❌"
            
        self.notification_frame.config(bg=bg_color)
        self.notification_label.config(bg=bg_color, text=f"{icon} {message}")
        
        # Tự động ẩn thông báo sau 5 giây (trừ thông báo lỗi)
        if msg_type != "error":
            self.root.after(5000, self.clear_notification)

    def clear_notification(self):
        """Xóa thông báo"""
        self.notification_frame.config(bg='#34495e')
        self.notification_label.config(bg='#34495e', text='')

    def update_player_status(self, player_id, is_ready):
        """Cập nhật trạng thái người chơi"""
        self.players_ready[player_id] = is_ready
        
        # Cập nhật giao diện
        players = list(self.players_ready.keys())
        if len(players) >= 1:
            status1 = "🟢 Sẵn sàng" if self.players_ready[players[0]] else "🔴 Chưa sẵn sàng"
            color1 = "#27ae60" if self.players_ready[players[0]] else "#e74c3c"
            self.player1_status.config(text=f'{players[0]}: {status1}', fg=color1)
            
        if len(players) >= 2:
            status2 = "🟢 Sẵn sàng" if self.players_ready[players[1]] else "🔴 Chưa sẵn sàng"
            color2 = "#27ae60" if self.players_ready[players[1]] else "#e74c3c"
            self.player2_status.config(text=f'{players[1]}: {status2}', fg=color2)
        else:
            # Reset player 2 nếu chỉ có 1 người chơi
            self.player2_status.config(text='Người chơi 2: 🔴 Chưa sẵn sàng', fg='#e74c3c')
        
        # Kiểm tra nếu cả hai đều sẵn sàng
        if len(self.players_ready) == 2 and all(self.players_ready.values()):
            self.game_status.config(text="🟢 Cả hai đã sẵn sàng! Game sẽ bắt đầu...", fg="#27ae60")
            self.show_notification("Cả hai người chơi đã sẵn sàng! Trận đấu sẽ bắt đầu... 🎮", "success")
        elif len(self.players_ready) == 2:
            not_ready_players = [p for p, ready in self.players_ready.items() if not ready]
            self.game_status.config(text="🔴 Đang chờ người chơi sẵn sàng...", fg="#e74c3c")
            self.show_notification(f"{', '.join(not_ready_players)} chưa sẵn sàng ⏳", "warning")
        else:
            self.game_status.config(text="🟡 Đang chờ người chơi khác...", fg="#f39c12")

    def start_game(self):
        """Bắt đầu game khi cả hai đã sẵn sàng"""
        if len(self.players_ready) == 2 and all(self.players_ready.values()):
            self.game_started = True
            self.game_ended = False
            self.show_notification("🎮 Trận đấu bắt đầu! Lượt đi đầu tiên...", "success")
            self.game_status.config(text="🎮 Game đang diễn ra...", fg="#9b59b6")
            # VÔ HIỆU HÓA nút sẵn sàng khi game bắt đầu
            self.ready_btn.config(state='disabled')
            # Gửi thông báo bắt đầu game tới server
            try:
                self.conn.send('START_GAME', {'room': self.current_room})
            except Exception as e:
                print(f"Lỗi gửi bắt đầu game: {e}")

    def connect(self):
        if self.conn:
            self.show_notification("Đã kết nối tới server rồi! 🟢", "info")
            return
        try:
            self.show_notification("Đang kết nối tới server... ⏳", "info")
            self.conn = ClientConnection(HOST, PORT, self.player_id, lambda m: self.q.put(m))
            self.conn.connect()
            
            # Cập nhật giao diện khi kết nối thành công
            self.status_lbl.config(text='🟢 Đã kết nối server', fg='#27ae60')
            self.connect_btn.config(style='Connected.TButton', text='🔗 Đã kết nối')
            
            # Kích hoạt các nút chức năng
            self.create_btn.config(state='normal')
            self.join_btn.config(state='normal')
            self.leave_btn.config(state='normal')
            self.ready_btn.config(state='normal', style='Accent.TButton')
            
            self.show_notification("Kết nối server thành công! 🎉", "success")
            self.refresh_rooms()
        except Exception as e:
            # Nếu kết nối thất bại, thử lại nhẹ (non-blocking) sau 2s
            self.show_notification(f"Không thể kết nối: {e}. Thử lại sau 2s...", "warning")
            self.root.after(2000, lambda: self.connect())
            return

    def create_room(self):
        if not self.conn:
            self.show_notification("Vui lòng kết nối tới server trước! 🔗", "warning")
            return
        room = simpledialog.askstring("Tạo phòng mới", "🎪 Nhập tên phòng:")
        if room:
            try:
                self.conn.send('CREATE_ROOM', {'room': room})
                self.show_notification(f"Đang tạo phòng '{room}'... ⏳", "info")
            except Exception as e:
                self.show_notification(f"Không thể tạo phòng: {e}", "error")

    def join_room(self):
        if not self.conn:
            self.show_notification("Vui lòng kết nối tới server trước! 🔗", "warning")
            return
        room = simpledialog.askstring("Tham gia phòng", "🎯 Nhập tên phòng:")
        if room:
            self.conn.send('JOIN_ROOM', {'room': room})

    def join_selected_room(self):
        sel = self.room_tree.selection()
        if not sel:
            self.show_notification("Vui lòng chọn một phòng từ danh sách! 📋", "warning")
            return
        item = sel[0]
        room_name = self.room_tree.item(item, 'values')[0]
        if room_name:
            self.conn.send('JOIN_ROOM', {'room': room_name})

    def leave_room(self):
        if not self.conn or not self.current_room:
            return
        try:
            self.conn.send('LEAVE', {})
            self.board = [[0]*self.size for _ in range(self.size)]
            self._draw_board()
            self.status_lbl.config(text='🟢 Đã kết nối server', fg='#27ae60')
            self.room_info_lbl.config(text='')
            self.current_room = None
            self.ready_btn.config(state='normal', style='Accent.TButton', text='⚡ Sẵn sàng')
            self.ready_status = False
            self.game_started = False
            self.game_ended = False
            self.players_ready = {}
            self.player1_status.config(text='Người chơi 1: 🔴 Chưa sẵn sàng', fg='#e74c3c')
            self.player2_status.config(text='Người chơi 2: 🔴 Chưa sẵn sàng', fg='#e74c3c')
            self.game_status.config(text='🟡 Đang chờ người chơi...', fg='#f39c12')
            self.show_notification("Bạn đã rời khỏi phòng! 👋", "info")
            self.refresh_rooms()
        except Exception as e:
            self.show_notification(f'Không thể rời phòng: {e}', "error")

    def refresh_rooms(self):
        if not self.conn:
            return
        try:
            self.conn.send('LIST_ROOMS', {})
        except Exception as e:
            self.show_notification(f'Không thể tải danh sách phòng: {e}', "error")

    def on_click(self, event):
        # Chỉ cho phép click khi game đã bắt đầu và chưa kết thúc
        winsound.PlaySound(CLICK_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self._animating or not self.conn or not self.game_started or self.game_ended:
            if not self.game_started:
                self.show_notification("Trận đấu chưa bắt đầu! Chờ cả hai người chơi sẵn sàng. ⏳", "warning")
            elif self.game_ended:
                self.show_notification("Trận đấu đã kết thúc! Bấm 'Chơi lại' để bắt đầu ván mới. 🔄", "info")
            return
            
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

    def _handle_msg(self, msg: dict):
        mtype = msg.get('type')
        payload = msg.get('payload', {})
        
        if mtype == 'ERROR':
            self.show_notification(payload.get('msg', 'Có lỗi xảy ra'), "error")
        
        elif mtype == 'ROOM_CREATED':
            room_name = payload.get('room')
            self.show_notification(f"Đã tạo phòng '{room_name}' thành công! 🎪", "success")
            self.current_room = room_name
            self.ready_btn.config(state='normal')
            self.room_info_lbl.config(text=f'Phòng: {room_name}')
            self.game_started = False
            self.game_ended = False
            # SỬA: Đảm bảo players_ready luôn có player hiện tại
            self.players_ready = {self.player_id: False}
            self.update_player_display()
            # THÊM: Làm mới danh sách phòng sau khi tạo phòng
            self.refresh_rooms()
            
        elif mtype == 'ROOM_JOINED':
            room_name = payload.get('room', '')
            players = payload.get('players', [])
            # SỬA: Nhận players_ready từ server
            players_ready = payload.get('players_ready', {})
            
            self.status_lbl.config(text=f'🟢 Đang trong phòng: {room_name}')
            self.room_info_lbl.config(text=f'Người chơi: {len(players)}/2')
            self.current_room = room_name
            self.ready_btn.config(state='normal')
            self.show_notification(f"Đã tham gia phòng '{room_name}'! 🎯", "success")
            
            # SỬA: Sử dụng players_ready từ server thay vì reset
            self.players_ready = players_ready
            # Đảm bảo player hiện tại luôn có trong danh sách
            if self.player_id not in self.players_ready:
                self.players_ready[self.player_id] = False
                
            self.update_player_display()
            # THÊM: Làm mới danh sách phòng sau khi tham gia phòng
            self.refresh_rooms()
            
        elif mtype == 'LIST_ROOMS_RESPONSE':
            rooms = payload.get('rooms', [])
            self._rooms = rooms
            
            # Cập nhật treeview
            for iid in self.room_tree.get_children():
                self.room_tree.delete(iid)
                
            for r in rooms:
                name = r.get('room', '')
                players = r.get('players', 0)
                creator = r.get('creator', '')
                self.room_tree.insert('', tk.END, values=(name, players, creator))
            
            # Cập nhật số lượng phòng
            self.room_count_lbl.config(text=f'{len(rooms)} phòng')
            
        elif mtype == 'PLAYER_JOINED':
            player = payload.get('player')
            players_ready = payload.get('players_ready', {})
            self.show_notification(f"Người chơi {player} đã tham gia phòng", "info")
            # SỬA: Cập nhật players_ready từ server
            self.players_ready = players_ready
            self.update_player_display()
            # THÊM: Làm mới danh sách phòng khi có người chơi mới
            self.refresh_rooms()
            
        elif mtype == 'PLAYER_LEFT':
            player = payload.get('player')
            players_ready = payload.get('players_ready', {})
            self.show_notification(f"Người chơi {player} đã rời phòng", "warning")
            # SỬA: Cập nhật players_ready từ server
            self.players_ready = players_ready
            self.update_player_display()
            self.game_started = False
            self.game_ended = False
            # KÍCH HOẠT LẠI nút sẵn sàng khi có người rời phòng
            self.ready_btn.config(state='normal')
            # THÊM: Làm mới danh sách phòng khi có người rời
            self.refresh_rooms()
            
        elif mtype == 'GAME_STATE':
            board = payload.get('board', [])
            self.board = board
            self._draw_board()
            
            if payload.get('winner'):
                winner = payload.get('winner')
                self.game_started = False
                self.game_ended = True
                # KÍCH HOẠT LẠI nút sẵn sàng khi game kết thúc
                winsound.PlaySound(WIN_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
                self.ready_btn.config(state='normal')
                
                win_coords = self.find_winning_line(self.board, win_len=5)
                if win_coords:
                    def after_anim():
                        self.show_notification(f"🎉 Người chơi {winner} đã thắng! Trận đấu kết thúc.", "success")
                        self.game_status.config(text=f"🏆 {winner} thắng!", fg="#e67e22")

                        # Hiển thị popup thông báo thắng / thua cho người chơi hiện tại
                        try:
                            players = list(self.players_ready.keys())
                            # Nếu có danh sách người chơi, ánh xạ số (1/2) -> player_id
                            if len(players) >= winner:
                                winner_name = players[winner-1]
                            else:
                                winner_name = f'Người chơi {winner}'

                            # Xác định index của người chơi hiện tại (1 hoặc 2)
                            if self.player_id in players:
                                my_index = players.index(self.player_id) + 1
                            else:
                                my_index = None

                            # Hiển thị popup kết thúc trận (giao diện lớn hơn, có nút rematch)
                            self.show_endgame_popup(my_index is not None and my_index == winner, winner_name)
                        except Exception:
                            # Không để lỗi popup làm hỏng luồng GUI
                            pass
                    self.animate_win(win_coords, callback=after_anim)
                else:
                    self.show_notification(f"🎉 Người chơi {winner} đã thắng! Trận đấu kết thúc.", "success")
                    self.game_status.config(text=f"🏆 {winner} thắng!", fg="#e67e22")

                    # Popup nếu không có animation
                    try:
                        players = list(self.players_ready.keys())
                        if len(players) >= winner:
                            winner_name = players[winner-1]
                        else:
                            winner_name = f'Người chơi {winner}'

                        if self.player_id in players and players.index(self.player_id) + 1 == winner:
                            self.show_endgame_popup(True, winner_name)
                        else:
                            self.show_endgame_popup(False, winner_name)
                    except Exception:
                        pass
            else:
                # Game đang diễn ra
                self.game_ended = False
                
        elif mtype == 'PLAYER_READY':
            # SỬA: Xử lý cả trường hợp payload chứa players_ready (danh sách đầy đủ)
            if 'players_ready' in payload:
                self.players_ready = payload['players_ready']
                self.update_player_display()
            else:
                player = payload.get('player')
                is_ready = payload.get('ready', False)
                self.update_player_status(player, is_ready)
                if is_ready:
                    self.show_notification(f"Người chơi {player} đã sẵn sàng! ⚡", "info")
                else:
                    self.show_notification(f"Người chơi {player} đã hủy sẵn sàng", "warning")
                    
        elif mtype == 'GAME_START':
            self.game_started = True
            self.game_ended = False
            # VÔ HIỆU HÓA nút sẵn sàng khi game bắt đầu
            self.ready_btn.config(state='disabled')
            self.show_notification("🎮 Trận đấu bắt đầu! Lượt đi đầu tiên...", "success")
            self.game_status.config(text="🎮 Game đang diễn ra...", fg="#9b59b6")

    def update_player_display(self):
        """Cập nhật hiển thị trạng thái người chơi"""
        players = list(self.players_ready.keys())
        
        if len(players) >= 1:
            status1 = "🟢 Sẵn sàng" if self.players_ready[players[0]] else "🔴 Chưa sẵn sàng"
            color1 = "#27ae60" if self.players_ready[players[0]] else "#e74c3c"
            self.player1_status.config(text=f'{players[0]}: {status1}', fg=color1)
        else:
            self.player1_status.config(text='Người chơi 1: 🔴 Chưa sẵn sàng', fg='#e74c3c')
            
        if len(players) >= 2:
            status2 = "🟢 Sẵn sàng" if self.players_ready[players[1]] else "🔴 Chưa sẵn sàng"
            color2 = "#27ae60" if self.players_ready[players[1]] else "#e74c3c"
            self.player2_status.config(text=f'{players[1]}: {status2}', fg=color2)
        else:
            self.player2_status.config(text='Người chơi 2: 🔴 Chưa sẵn sàng', fg='#e74c3c')
            
        # Cập nhật trạng thái game
        if len(players) < 2:
            self.game_status.config(text="🟡 Đang chờ người chơi khác...", fg="#f39c12")
            self.game_started = False
            self.game_ended = False

    def show_endgame_popup(self, is_winner: bool, winner_name: str):
        """Hiển thị popup kết thúc trận (Toplevel) với giao diện lớn, nút Rematch và Đóng."""
        try:
            win = tk.Toplevel(self.root)
            win.transient(self.root)
            win.grab_set()
            win.title('Kết thúc trận đấu')
            win.geometry('520x300')
            win.resizable(False, False)

            # Background frame
            bg_color = '#2ecc71' if is_winner else '#e74c3c'
            header = tk.Frame(win, bg=bg_color, height=140)
            header.pack(fill=tk.BOTH)

            # Big icon and title
            icon = '🏆' if is_winner else '💀'
            title_text = 'Bạn chiến thắng!' if is_winner else 'Bạn đã thua'
            title_lbl = tk.Label(header, text=f'{icon} {title_text}', font=('Segoe UI', 24, 'bold'), bg=bg_color, fg='white')
            title_lbl.pack(pady=(20, 5))

            sub_lbl = tk.Label(header, text=f'Người thắng: {winner_name}', font=('Segoe UI', 14), bg=bg_color, fg='white')
            sub_lbl.pack()

            # Body with details and buttons
            body = tk.Frame(win, bg='white')
            body.pack(fill=tk.BOTH, expand=True)

            info = tk.Label(body, text='Bạn có thể yêu cầu chơi lại hoặc quay về phòng.', font=('Segoe UI', 11), bg='white')
            info.pack(pady=16)

            btn_frame = tk.Frame(body, bg='white')
            btn_frame.pack(pady=8)

            def on_rematch():
                try:
                    self.request_rematch()
                except Exception:
                    pass
                win.destroy()

            def on_close():
                try:
                    win.destroy()
                except Exception:
                    pass

            rematch_btn = ttk.Button(btn_frame, text='🔁 Chơi lại', command=on_rematch, width=14)
            rematch_btn.pack(side=tk.LEFT, padx=10)

            close_btn = ttk.Button(btn_frame, text='✖ Đóng', command=on_close, width=14)
            close_btn.pack(side=tk.LEFT, padx=10)

            # Căn giữa cửa sổ so với gốc
            self.root.update_idletasks()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            ww = 520
            wh = 300
            x = rx + max((rw - ww) // 2, 0)
            y = ry + max((rh - wh) // 2, 0)
            win.geometry(f'{ww}x{wh}+{x}+{y}')

        except Exception:
            try:
                if is_winner:
                    messagebox.showinfo('Bạn thắng!', f'Chúc mừng — bạn thắng! ({winner_name})')
                else:
                    messagebox.showinfo('Bạn thua', f'Bạn thua. Người thắng: {winner_name}')
            except Exception:
                pass

    def _draw_board(self):
        self.canvas.delete('stone')
        
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        grid_pix = self.size * self.cell
        ox = max((cw - grid_pix) // 2, 0)
        oy = max((ch - grid_pix) // 2, 0)

        stone_size = self.cell * 0.8
        pad = (self.cell - stone_size) / 2
        
        for y in range(self.size):
            for x in range(self.size):
                v = self.board[y][x]
                if v != 0:
                    x1 = ox + x * self.cell + pad
                    y1 = oy + y * self.cell + pad
                    x2 = x1 + stone_size
                    y2 = y1 + stone_size
                    
                    if v == 1:
                        self.canvas.create_oval(x1, y1, x2, y2, fill='#2c3e50', outline='#1a252f', width=2, tags='stone')
                        self.canvas.create_oval(x1+2, y1+2, x2-2, y2-2, outline='#34495e', width=1, tags='stone')
                    else:
                        self.canvas.create_oval(x1, y1, x2, y2, fill='#ecf0f1', outline='#bdc3c7', width=2, tags='stone')
                        self.canvas.create_oval(x1+2, y1+2, x2-2, y2-2, outline='white', width=1, tags='stone')

    def _draw_grid(self):
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
            new_cell = max(20, int(min(event.width, event.height) / self.size))
        except:
            new_cell = self.cell
            
        if new_cell != self.cell:
            self.cell = new_cell
            
        self._draw_grid()
        self._draw_board()

    def find_winning_line(self, board, win_len=5):
        H = len(board)
        W = len(board[0]) if H > 0 else 0
        dirs = [(1,0), (0,1), (1,1), (1,-1)]
        
        for y in range(H):
            for x in range(W):
                v = board[y][x]
                if v == 0:
                    continue
                for dx, dy in dirs:
                    coords = [(x,y)]
                    nx, ny = x + dx, y + dy
                    while 0 <= nx < W and 0 <= ny < H and board[ny][nx] == v:
                        coords.append((nx, ny))
                        nx += dx
                        ny += dy
                    bx, by = x - dx, y - dy
                    while 0 <= bx < W and 0 <= by < H and board[by][bx] == v:
                        coords.insert(0, (bx, by))
                        bx -= dx
                        by -= dy
                    if len(coords) >= win_len:
                        return coords
        return []

    def animate_win(self, coords, callback=None, cycles=6, interval=300):
        if not coords:
            if callback:
                callback()
            return
            
        self._animating = True
        highlight_color = '#e74c3c'
        
        step = {'count': 0}
        
        def pulse():
            step['count'] += 1
            make_highlight = (step['count'] % 2 == 1)
            
            for x, y in coords:
                tag = f'cell_{x}_{y}'
                items = self.canvas.find_withtag(tag)
                for item in items:
                    if make_highlight:
                        self.canvas.itemconfig(item, fill=highlight_color)
                    else:
                        self.canvas.itemconfig(item, fill=self.board_bg)
            
            if step['count'] < cycles * 2:
                self.root.after(interval // 2, pulse)
            else:
                for x, y in coords:
                    tag = f'cell_{x}_{y}'
                    items = self.canvas.find_withtag(tag)
                    for item in items:
                        self.canvas.itemconfig(item, fill=self.board_bg)
                self._animating = False
                if callback:
                    callback()
        
        pulse()

    def request_rematch(self):
        """Gửi yêu cầu chơi lại (rematch) tới server."""
        if not self.conn or not self.current_room:
            self.show_notification("Bạn phải ở trong phòng để yêu cầu chơi lại.", "warning")
            return
        try:
    
            self.conn.send('REPLAY_REQUEST', {'room': self.current_room})
            self.show_notification("Đã gửi yêu cầu chơi lại tới đối thủ.", "info")
        except Exception as e:
            self.show_notification(f'Không thể gửi yêu cầu chơi lại: {e}', "error")

    def on_close(self):
        """Gửi LEAVE (nếu đang trong phòng) và đóng cửa sổ."""
        try:
            if self.conn:
                if self.current_room:
                    try:
                        self.conn.send('LEAVE', {})
                    except Exception:
                        pass
                # Nếu ClientConnection có method close/disconnect, gọi ở đây (tùy implementation)
                if hasattr(self.conn, 'close'):
                    try:
                        self.conn.close()
                    except Exception:
                        pass
        finally:
            self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('1100x700')
    root.minsize(900, 600)
    app = CaroGUI(root)
    root.mainloop()