
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
