"""终端标签页管理 - Windows 优化版"""

import tkinter as tk

from src_win.gui.terminal_widget import TerminalWidget
from src_win.storage import Connection


class TerminalNotebook:
    """终端标签页 - Windows 风格"""

    # 深色主题配色
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

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        # 标签栏
        self.tab_bar = tk.Frame(self.frame, bg=self.TAB_BG, height=32)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)

        # 内容区域
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
        """打开新连接 (兼容接口)"""
        self.add_terminal(conn)

    def add_terminal(self, connection: Connection):
        """添加终端标签页"""
        # 隐藏欢迎页
        if hasattr(self, '_welcome_frame') and self._welcome_frame.winfo_exists():
            self._welcome_frame.destroy()

        for widget in self.content.winfo_children():
            widget.pack_forget()

        terminal = TerminalWidget(self.content, connection, on_connected=self._on_terminal_connected)

        # 创建标签
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

        # 保存引用
        tab_frame.terminal = terminal
        tab_frame.label = label
        tab_frame.close_btn = close_btn

        self._tab_frames.append((tab_frame, terminal))
        self._select_tab(tab_frame, terminal)
        terminal.connect()

    def _select_tab(self, tab_frame, terminal):
        """选中标签页"""
        # 重置所有标签样式
        for tf, _ in self._tab_frames:
            tf.configure(bg=self.TAB_BG)
            for child in tf.winfo_children():
                if isinstance(child, tk.Label):
                    if child.cget('text') == '×':
                        child.configure(bg=self.TAB_BG, fg='#808080')
                    else:
                        child.configure(bg=self.TAB_BG, fg=self.TAB_TEXT)

        # 激活当前标签
        tab_frame.configure(bg=self.TAB_ACTIVE)
        for child in tab_frame.winfo_children():
            if isinstance(child, tk.Label):
                if child.cget('text') == '×':
                    child.configure(bg=self.TAB_ACTIVE, fg='#808080')
                else:
                    child.configure(bg=self.TAB_ACTIVE, fg=self.TAB_TEXT_ACTIVE)

        # 显示终端内容
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

    def close_current(self):
        """关闭当前标签"""
        if self._current_tab:
            tab_frame, terminal = self._current_tab
            if (tab_frame, terminal) in self._tab_frames:
                self._close_tab(tab_frame, terminal)
