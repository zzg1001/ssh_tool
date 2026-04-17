"""终端标签页管理 - Windows 优化版 - 支持拖出拖回"""

import tkinter as tk
import threading

from src_win.gui.terminal_widget import TerminalWidget
from src_win.storage import Connection


class TerminalNotebook:
    """终端标签页 - Windows 风格 - 支持拖出拖回"""

    BG_COLOR = '#1e1e1e'
    TAB_BG = '#2d2d2d'
    TAB_ACTIVE = '#1e1e1e'
    TAB_TEXT = '#cccccc'
    TAB_TEXT_ACTIVE = '#ffffff'
    CLOSE_HOVER = '#e81123'

    def __init__(self, parent, main_window=None):
        self.frame = tk.Frame(parent, bg=self.BG_COLOR)
        self.main_window = main_window
        self._tab_frames: list = []
        self._current_tab = None
        self._detached_windows: list = []

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        self.tab_bar = tk.Frame(self.frame, bg=self.TAB_BG, height=32)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)

        self.content = tk.Frame(self.frame, bg=self.BG_COLOR)
        self.content.pack(fill=tk.BOTH, expand=True)

        self._show_welcome()

    def _show_welcome(self):
        """显示欢迎页"""
        for widget in self.content.winfo_children():
            widget.destroy()

        welcome = tk.Frame(self.content, bg=self.BG_COLOR)
        welcome.pack(fill=tk.BOTH, expand=True)

        center = tk.Frame(welcome, bg=self.BG_COLOR)
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(center, text="zzgShell", bg=self.BG_COLOR, fg='#0078d4',
                 font=('Segoe UI Light', 42)).pack()
        tk.Label(center, text="双击左侧连接开始 SSH 会话", bg=self.BG_COLOR, fg='#666666',
                 font=('Segoe UI', 12)).pack(pady=(16, 0))

        self._welcome_frame = welcome

    def open_connection(self, conn: Connection):
        """打开新连接"""
        self.add_terminal(conn)

    def add_terminal(self, connection: Connection):
        """添加终端标签页"""
        if hasattr(self, '_welcome_frame') and self._welcome_frame.winfo_exists():
            self._welcome_frame.destroy()

        for widget in self.content.winfo_children():
            widget.pack_forget()

        terminal = TerminalWidget(self.content, connection, on_connected=self._on_terminal_connected)

        tab_frame = tk.Frame(self.tab_bar, bg=self.TAB_BG)
        tab_frame.pack(side=tk.LEFT, padx=(1, 0), pady=(4, 0))

        label = tk.Label(
            tab_frame,
            text=f"  {connection.name}  ",
            bg=self.TAB_BG,
            fg=self.TAB_TEXT,
            font=('Segoe UI', 9)
        )
        label.pack(side=tk.LEFT, padx=(8, 0), pady=(4, 4))

        close_btn = tk.Label(
            tab_frame,
            text="×",
            bg=self.TAB_BG,
            fg='#808080',
            font=('Segoe UI', 11)
        )
        close_btn.pack(side=tk.LEFT, padx=(2, 8), pady=(4, 4))

        def on_select(e):
            self._select_tab(tab_frame, terminal)

        def on_close(e):
            self._close_tab(tab_frame, terminal)
            return "break"

        def on_enter(e):
            close_btn.configure(fg='#ffffff', bg=self.CLOSE_HOVER)

        def on_leave(e):
            close_btn.configure(fg='#808080', bg=tab_frame.cget('bg'))

        tab_frame.bind('<Button-1>', on_select)
        label.bind('<Button-1>', on_select)
        close_btn.bind('<Button-1>', on_close)
        close_btn.bind('<Enter>', on_enter)
        close_btn.bind('<Leave>', on_leave)

        self._setup_tab_drag(tab_frame, label, terminal, connection.name)

        tab_frame.terminal = terminal
        tab_frame.label = label
        tab_frame.close_btn = close_btn
        tab_frame.tab_name = connection.name

        # 终端获得焦点时更新 Files 面板
        terminal.terminal.bind('<FocusIn>', lambda e, t=terminal: self._on_terminal_focus(t))
        terminal.terminal.bind('<Button-1>', lambda e, t=terminal: self._on_terminal_focus(t))

        self._tab_frames.append((tab_frame, terminal))
        self._select_tab(tab_frame, terminal)
        terminal.connect()

    def _setup_tab_drag(self, tab_frame, label, terminal, name):
        """设置标签拖动功能"""
        drag_data = {'dragging': False, 'start_x': 0, 'start_y': 0}

        def on_drag_start(e):
            drag_data['dragging'] = True
            drag_data['start_x'] = e.x_root
            drag_data['start_y'] = e.y_root

        def on_drag_motion(e):
            if not drag_data['dragging']:
                return
            dy = abs(e.y_root - drag_data['start_y'])
            if dy > 50:
                drag_data['dragging'] = False
                self._detach_tab(tab_frame, terminal, name, e.x_root, e.y_root)

        def on_drag_end(e):
            drag_data['dragging'] = False

        label.bind('<ButtonPress-1>', on_drag_start)
        label.bind('<B1-Motion>', on_drag_motion)
        label.bind('<ButtonRelease-1>', on_drag_end)
        tab_frame.bind('<B1-Motion>', on_drag_motion)

    def _detach_tab(self, tab_frame, terminal, name, x, y):
        """分离标签到新窗口"""
        ssh_client = terminal.ssh_client
        connection = terminal.connection

        if not ssh_client or not ssh_client.channel:
            return

        self._tab_frames = [(tf, t) for tf, t in self._tab_frames if tf != tab_frame]
        tab_frame.destroy()

        terminal._running = False
        terminal._stats_running = False
        terminal.ssh_client = None
        terminal.frame.destroy()

        detached = DetachedTerminalWindow(
            self, name, connection, ssh_client, x, y
        )
        self._detached_windows.append(detached)

        if self._tab_frames:
            self._select_tab(*self._tab_frames[-1])
        else:
            self._current_tab = None
            self._show_welcome()

        # 分离窗口创建后，更新 Files 面板到该窗口的连接
        if self.main_window and ssh_client:
            self.main_window.update_sftp_panel(ssh_client)

    def reattach_terminal(self, name, connection, ssh_client, detached_window):
        """将分离的终端重新附加到主窗口"""
        if detached_window in self._detached_windows:
            self._detached_windows.remove(detached_window)

        if hasattr(self, '_welcome_frame') and self._welcome_frame.winfo_exists():
            self._welcome_frame.destroy()

        for widget in self.content.winfo_children():
            widget.pack_forget()

        new_terminal = TerminalWidget(self.content, connection)

        # 终端获得焦点时更新 Files 面板
        new_terminal.terminal.bind('<FocusIn>', lambda e, t=new_terminal: self._on_terminal_focus(t))
        new_terminal.terminal.bind('<Button-1>', lambda e, t=new_terminal: self._on_terminal_focus(t))

        tab_frame = tk.Frame(self.tab_bar, bg=self.TAB_BG)
        tab_frame.pack(side=tk.LEFT, padx=(1, 0), pady=(4, 0))

        label = tk.Label(tab_frame, text=f"  {name}  ", bg=self.TAB_BG,
                        fg=self.TAB_TEXT, font=('Segoe UI', 9))
        label.pack(side=tk.LEFT, padx=(8, 0), pady=(4, 4))

        close_btn = tk.Label(tab_frame, text="×", bg=self.TAB_BG,
                            fg='#808080', font=('Segoe UI', 11))
        close_btn.pack(side=tk.LEFT, padx=(2, 8), pady=(4, 4))

        def on_select(e):
            self._select_tab(tab_frame, new_terminal)

        def on_close(e):
            self._close_tab(tab_frame, new_terminal)
            return "break"

        tab_frame.bind('<Button-1>', on_select)
        label.bind('<Button-1>', on_select)
        close_btn.bind('<Button-1>', on_close)
        close_btn.bind('<Enter>', lambda e: close_btn.configure(fg='#ffffff', bg=self.CLOSE_HOVER))
        close_btn.bind('<Leave>', lambda e: close_btn.configure(fg='#808080', bg=tab_frame.cget('bg')))

        self._setup_tab_drag(tab_frame, label, new_terminal, name)

        tab_frame.terminal = new_terminal
        tab_frame.label = label
        tab_frame.close_btn = close_btn
        tab_frame.tab_name = name

        new_terminal.ssh_client = ssh_client
        new_terminal._running = True
        new_terminal._set_status("已连接", new_terminal.STATUS_CONNECTED)
        new_terminal._start_stats_monitor()
        threading.Thread(target=new_terminal._read_loop, daemon=True).start()

        self._tab_frames.append((tab_frame, new_terminal))
        self._select_tab(tab_frame, new_terminal)

        # 更新 SFTP 面板
        if self.main_window and ssh_client:
            self.main_window.update_sftp_panel(ssh_client)

    def _is_over_tab_bar(self, x, y):
        """检查坐标是否在标签栏上方"""
        try:
            bar_x = self.tab_bar.winfo_rootx()
            bar_y = self.tab_bar.winfo_rooty()
            bar_w = self.tab_bar.winfo_width()
            bar_h = self.tab_bar.winfo_height()
            return bar_x <= x <= bar_x + bar_w and bar_y <= y <= bar_y + bar_h + 20
        except:
            return False

    def _is_near_tab_bar(self, window_x, window_y):
        """检查窗口是否靠近标签栏（用于自动合并）"""
        try:
            bar_x = self.tab_bar.winfo_rootx()
            bar_y = self.tab_bar.winfo_rooty()
            bar_w = self.tab_bar.winfo_width()
            bar_h = self.tab_bar.winfo_height()

            # 水平方向：窗口中心在标签栏水平范围附近
            window_center_x = window_x + 200  # 假设窗口宽度约400，取中心
            in_x_range = (bar_x - 100) <= window_center_x <= (bar_x + bar_w + 100)

            # 垂直方向：窗口顶部在标签栏上下 100 像素内
            bar_center_y = bar_y + bar_h // 2
            in_y_range = abs(window_y - bar_center_y) < 100

            return in_x_range and in_y_range
        except:
            return False

    def _select_tab(self, tab_frame, terminal):
        """选中标签页"""
        for tf, _ in self._tab_frames:
            tf.configure(bg=self.TAB_BG)
            for child in tf.winfo_children():
                if isinstance(child, tk.Label):
                    if child.cget('text') == '×':
                        child.configure(bg=self.TAB_BG, fg='#808080')
                    else:
                        child.configure(bg=self.TAB_BG, fg=self.TAB_TEXT)

        tab_frame.configure(bg=self.TAB_ACTIVE)
        for child in tab_frame.winfo_children():
            if isinstance(child, tk.Label):
                if child.cget('text') == '×':
                    child.configure(bg=self.TAB_ACTIVE, fg='#808080')
                else:
                    child.configure(bg=self.TAB_ACTIVE, fg=self.TAB_TEXT_ACTIVE)

        for widget in self.content.winfo_children():
            widget.pack_forget()

        terminal.frame.pack(fill=tk.BOTH, expand=True)
        terminal.focus()
        self._current_tab = (tab_frame, terminal)

        if self.main_window and terminal.ssh_client:
            self.main_window.update_sftp_panel(terminal.ssh_client)

    def _close_tab(self, tab_frame, terminal):
        """关闭标签页"""
        terminal.disconnect()
        terminal.frame.destroy()
        tab_frame.destroy()
        self._tab_frames = [(tf, t) for tf, t in self._tab_frames if tf != tab_frame]

        if self._tab_frames:
            self._select_tab(*self._tab_frames[-1])
        else:
            self._current_tab = None
            self._show_welcome()
            if self.main_window:
                self.main_window.update_sftp_panel(None)

    def _on_terminal_connected(self, ssh_client):
        """终端连接成功回调"""
        if self.main_window:
            self.main_window.update_sftp_panel(ssh_client)

    def _on_terminal_focus(self, terminal):
        """终端获得焦点时更新 Files 面板"""
        if self.main_window and terminal.ssh_client:
            self.main_window.update_sftp_panel(terminal.ssh_client)

    def close_current(self):
        """关闭当前标签"""
        if self._current_tab:
            tab_frame, terminal = self._current_tab
            if (tab_frame, terminal) in self._tab_frames:
                self._close_tab(tab_frame, terminal)

    def close_all_detached(self):
        """关闭所有分离的窗口"""
        for win in self._detached_windows[:]:
            try:
                win.close()
            except:
                pass
        self._detached_windows.clear()


class DetachedTerminalWindow:
    """分离的终端窗口 - Windows 风格"""

    BG_COLOR = '#1e1e1e'
    TAB_BG = '#2d2d2d'

    def __init__(self, notebook, name, connection, ssh_client, x, y):
        self.notebook = notebook
        self.name = name
        self.connection = connection
        self.ssh_client = ssh_client
        self.terminal = None

        self.window = tk.Toplevel(notebook.frame)
        self.window.title(f"zzgShell - {name}")
        self.window.geometry(f"900x600+{x-100}+{y-50}")
        self.window.configure(bg=self.BG_COLOR)

        self._setup_ui()
        self._setup_drag()

        self.window.protocol("WM_DELETE_WINDOW", self.close)

        # 当窗口获得焦点时，更新主窗口的 Files 面板
        self.window.bind('<FocusIn>', self._on_focus)

    def _setup_ui(self):
        """设置界面"""
        self.title_bar = tk.Frame(self.window, bg=self.TAB_BG, height=32)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)

        title_label = tk.Label(
            self.title_bar,
            text=f"  ↩ {self.name}  (拖动放回主窗口)",
            bg=self.TAB_BG,
            fg='#d4d4d4',
            font=('Segoe UI', 9)
        )
        title_label.pack(side=tk.LEFT, padx=8, pady=6)

        close_btn = tk.Label(
            self.title_bar,
            text="×",
            bg=self.TAB_BG,
            fg='#808080',
            font=('Segoe UI', 14)
        )
        close_btn.pack(side=tk.RIGHT, padx=10, pady=4)
        close_btn.bind('<Button-1>', lambda e: self.close())
        close_btn.bind('<Enter>', lambda e: close_btn.configure(fg='#ffffff', bg='#e81123'))
        close_btn.bind('<Leave>', lambda e: close_btn.configure(fg='#808080', bg=self.TAB_BG))

        self.terminal = TerminalWidget(self.window, self.connection)
        self.terminal.frame.pack(fill=tk.BOTH, expand=True)

        self.terminal.ssh_client = self.ssh_client
        self.terminal._running = True
        self.terminal._set_status("已连接", self.terminal.STATUS_CONNECTED)
        self.terminal._start_stats_monitor()

        threading.Thread(target=self.terminal._read_loop, daemon=True).start()

        # 终端获得焦点时也更新 Files 面板
        self.terminal.terminal.bind('<FocusIn>', self._on_focus)
        self.terminal.terminal.bind('<Button-1>', self._on_focus)

    def _on_focus(self, event=None):
        """窗口获得焦点时更新 Files 面板"""
        if self.notebook.main_window and self.terminal and self.terminal.ssh_client:
            self.notebook.main_window.update_sftp_panel(self.terminal.ssh_client)

    def _setup_drag(self):
        """设置拖动功能"""
        drag_data = {'dragging': False, 'start_x': 0, 'start_y': 0}

        def on_drag_start(e):
            drag_data['dragging'] = True
            drag_data['start_x'] = e.x_root
            drag_data['start_y'] = e.y_root

        def on_drag_motion(e):
            if not drag_data['dragging']:
                return
            dx = e.x_root - drag_data['start_x']
            dy = e.y_root - drag_data['start_y']
            x = self.window.winfo_x() + dx
            y = self.window.winfo_y() + dy
            self.window.geometry(f"+{x}+{y}")
            drag_data['start_x'] = e.x_root
            drag_data['start_y'] = e.y_root

            # 检测窗口是否靠近主窗口标签栏，自动合并
            if self.notebook._is_near_tab_bar(x, y):
                drag_data['dragging'] = False
                self._reattach()

        def on_drag_end(e):
            drag_data['dragging'] = False

        self.title_bar.bind('<ButtonPress-1>', on_drag_start)
        self.title_bar.bind('<B1-Motion>', on_drag_motion)
        self.title_bar.bind('<ButtonRelease-1>', on_drag_end)

        for child in self.title_bar.winfo_children():
            if isinstance(child, tk.Label) and '×' not in child.cget('text'):
                child.bind('<ButtonPress-1>', on_drag_start)
                child.bind('<B1-Motion>', on_drag_motion)
                child.bind('<ButtonRelease-1>', on_drag_end)

    def _reattach(self):
        """重新附加到主窗口"""
        ssh_client = self.terminal.ssh_client
        self.terminal._running = False
        self.terminal._stats_running = False
        self.terminal.ssh_client = None

        self.window.destroy()

        self.notebook.reattach_terminal(
            self.name, self.connection, ssh_client, self
        )

    def close(self):
        """关闭窗口"""
        if self.terminal:
            self.terminal.disconnect()
        self.window.destroy()
        if self in self.notebook._detached_windows:
            self.notebook._detached_windows.remove(self)
