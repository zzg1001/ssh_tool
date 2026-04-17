"""终端标签页管理 - 支持拖出和拖回窗口"""

import tkinter as tk
import threading

from .terminal_widget import TerminalWidget
from ..storage import Connection


class TerminalNotebook:
    """终端标签页 - 支持拖出拖回"""

    def __init__(self, parent, main_window=None):
        self.frame = tk.Frame(parent, bg='#1e1e1e')
        self.main_window = main_window
        self._tab_frames: list = []
        self._current_tab = None
        self._detached_windows: list = []

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        self.tab_bar = tk.Frame(self.frame, bg='#2d2d2d', height=24)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)

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

        label = tk.Label(
            tab_frame,
            text=f" {name} ",
            bg='#2d2d2d',
            fg='#d4d4d4',
            font=('', 9)
        )
        label.pack(side=tk.LEFT, padx=(4, 0))

        close_btn = tk.Label(
            tab_frame,
            text="×",
            bg='#2d2d2d',
            fg='#808080',
            font=('', 10)
        )
        close_btn.pack(side=tk.LEFT, padx=(3, 5))

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

        self._setup_tab_drag(tab_frame, label, terminal, name)

        tab_frame.terminal = terminal
        tab_frame.label = label
        tab_frame.close_btn = close_btn
        tab_frame.tab_name = name
        self._tab_frames.append(tab_frame)

        return tab_frame

    def _setup_tab_drag(self, tab_frame, label, terminal, name):
        """设置标签拖动功能（拖出）"""
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

        if tab_frame in self._tab_frames:
            self._tab_frames.remove(tab_frame)
        tab_frame.destroy()

        terminal._running = False
        terminal._stats_running = False
        terminal.ssh_client = None
        terminal.frame.destroy()

        # 创建分离窗口
        detached = DetachedTerminalWindow(
            self, name, connection, ssh_client, x, y
        )
        self._detached_windows.append(detached)

        if self._tab_frames:
            last_tab = self._tab_frames[-1]
            self._select_tab(last_tab, last_tab.terminal)
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

        # 隐藏欢迎页
        if hasattr(self, '_welcome_frame') and self._welcome_frame.winfo_exists():
            self._welcome_frame.destroy()

        # 创建新终端
        new_terminal = TerminalWidget(self.content, connection)

        # 终端获得焦点时更新 Files 面板
        new_terminal.terminal.bind('<FocusIn>', lambda e, t=new_terminal: self._on_terminal_focus(t))
        new_terminal.terminal.bind('<Button-1>', lambda e, t=new_terminal: self._on_terminal_focus(t))

        tab_frame = self._create_tab_button(name, new_terminal)

        # 接管连接
        new_terminal.ssh_client = ssh_client
        new_terminal._running = True
        new_terminal._set_status("已连接", "#28a745")
        new_terminal._start_stats_monitor()
        threading.Thread(target=new_terminal._read_loop, daemon=True).start()

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

        if self.main_window and hasattr(terminal, 'ssh_client') and terminal.ssh_client:
            self.main_window.update_sftp_panel(terminal.ssh_client)

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

        # 终端获得焦点时更新 Files 面板
        terminal.terminal.bind('<FocusIn>', lambda e, t=terminal: self._on_terminal_focus(t))
        terminal.terminal.bind('<Button-1>', lambda e, t=terminal: self._on_terminal_focus(t))

        tab_frame = self._create_tab_button(conn.name, terminal)
        self._select_tab(tab_frame, terminal)
        terminal.connect()

    def _on_terminal_focus(self, terminal):
        """终端获得焦点时更新 Files 面板"""
        if self.main_window and terminal.ssh_client:
            self.main_window.update_sftp_panel(terminal.ssh_client)

    def close_current(self):
        """关闭当前标签"""
        if self._current_tab and self._current_tab in self._tab_frames:
            self._close_tab(self._current_tab, self._current_tab.terminal)

    def close_all_detached(self):
        """关闭所有分离的窗口"""
        for win in self._detached_windows[:]:
            try:
                win.close()
            except:
                pass
        self._detached_windows.clear()


class DetachedTerminalWindow:
    """分离的终端窗口 - 可拖回主窗口"""

    def __init__(self, notebook, name, connection, ssh_client, x, y):
        self.notebook = notebook
        self.name = name
        self.connection = connection
        self.ssh_client = ssh_client
        self.terminal = None

        # 创建窗口
        self.window = tk.Toplevel(notebook.frame)
        self.window.title(f"zzgShell - {name}")
        self.window.geometry(f"900x600+{x-100}+{y-50}")
        self.window.configure(bg='#1e1e1e')

        self._setup_ui()
        self._setup_drag()

        self.window.protocol("WM_DELETE_WINDOW", self.close)

        # 当窗口获得焦点时，更新主窗口的 Files 面板
        self.window.bind('<FocusIn>', self._on_focus)
        self.terminal.terminal.bind('<FocusIn>', self._on_focus)
        self.terminal.terminal.bind('<Button-1>', self._on_focus)

    def _setup_ui(self):
        """设置界面"""
        # 可拖动的标题栏
        self.title_bar = tk.Frame(self.window, bg='#2d2d2d', height=28)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)

        # 标题
        title_label = tk.Label(
            self.title_bar,
            text=f"  ↩ {self.name}  (拖动此处可放回主窗口)",
            bg='#2d2d2d',
            fg='#d4d4d4',
            font=('', 10)
        )
        title_label.pack(side=tk.LEFT, padx=8, pady=4)

        # 关闭按钮
        close_btn = tk.Label(
            self.title_bar,
            text="×",
            bg='#2d2d2d',
            fg='#808080',
            font=('', 14)
        )
        close_btn.pack(side=tk.RIGHT, padx=10, pady=4)
        close_btn.bind('<Button-1>', lambda e: self.close())
        close_btn.bind('<Enter>', lambda e: close_btn.configure(fg='#ff5555'))
        close_btn.bind('<Leave>', lambda e: close_btn.configure(fg='#808080'))

        # 终端
        self.terminal = TerminalWidget(self.window, self.connection)
        self.terminal.frame.pack(fill=tk.BOTH, expand=True)

        # 接管连接
        self.terminal.ssh_client = self.ssh_client
        self.terminal._running = True
        self.terminal._set_status("已连接", "#28a745")
        self.terminal._start_stats_monitor()

        import threading
        threading.Thread(target=self.terminal._read_loop, daemon=True).start()

    def _setup_drag(self):
        """设置拖动功能（拖回主窗口）"""
        drag_data = {'dragging': False, 'start_x': 0, 'start_y': 0}

        def on_drag_start(e):
            drag_data['dragging'] = True
            drag_data['start_x'] = e.x_root
            drag_data['start_y'] = e.y_root

        def on_drag_motion(e):
            if not drag_data['dragging']:
                return

            # 移动窗口
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

    def _on_focus(self, event=None):
        """窗口获得焦点时更新 Files 面板"""
        if self.notebook.main_window and self.terminal and self.terminal.ssh_client:
            self.notebook.main_window.update_sftp_panel(self.terminal.ssh_client)

    def _reattach(self):
        """重新附加到主窗口"""
        # 保存连接
        ssh_client = self.terminal.ssh_client
        self.terminal._running = False
        self.terminal._stats_running = False
        self.terminal.ssh_client = None

        # 关闭窗口
        self.window.destroy()

        # 重新附加
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
