"""终端标签页管理"""

import sys
import tkinter as tk

# 根据平台选择终端组件
if sys.platform == 'win32':
    from .terminal_widget_win import TerminalWidgetWin as TerminalWidget
else:
    from .terminal_widget import TerminalWidget

from ..storage import Connection


class TerminalNotebook:
    """终端标签页 - 带关闭按钮"""

    def __init__(self, parent, main_window=None):
        self.frame = tk.Frame(parent, bg='#1e1e1e')
        self.main_window = main_window
        self._tab_frames: list = []
        self._current_tab = None

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        # 标签页容器
        self.tab_bar = tk.Frame(self.frame, bg='#2d2d2d', height=24)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)

        # 内容区域
        self.content = tk.Frame(self.frame, bg='#1e1e1e')
        self.content.pack(fill=tk.BOTH, expand=True)

        self._show_welcome()

    def _show_welcome(self):
        """显示欢迎页"""
        for widget in self.content.winfo_children():
            widget.destroy()

        welcome = tk.Frame(self.content, bg='#1e1e1e')
        welcome.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(
            welcome,
            text="双击左侧连接开始 SSH 会话",
            bg='#1e1e1e',
            fg='#606060',
            font=('', 16)
        )
        label.pack(expand=True)

        self._welcome_frame = welcome

    def _create_tab_button(self, name: str, terminal: TerminalWidget):
        """创建标签按钮"""
        tab_frame = tk.Frame(self.tab_bar, bg='#2d2d2d')
        tab_frame.pack(side=tk.LEFT, padx=(0, 1), pady=2, ipady=1)

        # 标签名称
        label = tk.Label(
            tab_frame,
            text=f" {name} ",
            bg='#2d2d2d',
            fg='#d4d4d4',
            font=('', 9)
        )
        label.pack(side=tk.LEFT, padx=(4, 0))

        # 关闭按钮
        close_btn = tk.Label(
            tab_frame,
            text="×",
            bg='#2d2d2d',
            fg='#808080',
            font=('', 10)
        )
        close_btn.pack(side=tk.LEFT, padx=(3, 5))

        # 绑定事件
        def on_select(e):
            self._select_tab(tab_frame, terminal)

        def on_close(e):
            self._close_tab(tab_frame, terminal)
            return "break"

        def on_close_enter(e):
            close_btn.configure(fg='#ff5555')

        def on_close_leave(e):
            close_btn.configure(fg='#808080')

        tab_frame.bind('<Button-1>', on_select)
        label.bind('<Button-1>', on_select)
        close_btn.bind('<Button-1>', on_close)
        close_btn.bind('<Enter>', on_close_enter)
        close_btn.bind('<Leave>', on_close_leave)

        # 保存引用
        tab_frame.terminal = terminal
        tab_frame.label = label
        tab_frame.close_btn = close_btn
        self._tab_frames.append(tab_frame)

        return tab_frame

    def _select_tab(self, tab_frame, terminal: TerminalWidget):
        """选中标签"""
        for tf in self._tab_frames:
            tf.configure(bg='#2d2d2d')
            tf.label.configure(bg='#2d2d2d', fg='#d4d4d4')
            tf.close_btn.configure(bg='#2d2d2d')

        tab_frame.configure(bg='#1e1e1e')
        tab_frame.label.configure(bg='#1e1e1e', fg='#ffffff')
        tab_frame.close_btn.configure(bg='#1e1e1e')

        for widget in self.content.winfo_children():
            widget.pack_forget()
        terminal.frame.pack(fill=tk.BOTH, expand=True)

        self._current_tab = tab_frame

    def _close_tab(self, tab_frame, terminal: TerminalWidget):
        """关闭标签"""
        terminal.disconnect()

        if tab_frame in self._tab_frames:
            self._tab_frames.remove(tab_frame)
        tab_frame.destroy()
        terminal.frame.destroy()

        if self._tab_frames:
            last_tab = self._tab_frames[-1]
            self._select_tab(last_tab, last_tab.terminal)
        else:
            self._current_tab = None
            self._show_welcome()
            if self.main_window:
                self.main_window.update_sftp_panel(None)

    def open_connection(self, conn: Connection):
        """打开新连接"""
        if hasattr(self, '_welcome_frame') and self._welcome_frame.winfo_exists():
            self._welcome_frame.destroy()

        def on_connected(ssh_client):
            if self.main_window:
                self.main_window.update_sftp_panel(ssh_client)

        terminal = TerminalWidget(self.content, conn, on_connected=on_connected)
        tab_frame = self._create_tab_button(conn.name, terminal)
        self._select_tab(tab_frame, terminal)
        terminal.connect()

    def close_current(self):
        """关闭当前标签"""
        if self._current_tab and self._current_tab in self._tab_frames:
            self._close_tab(self._current_tab, self._current_tab.terminal)
