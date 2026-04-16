"""主窗口 - 白色主题"""

import tkinter as tk

try:
    from tkinterdnd2 import TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

from .left_panel import LeftPanel
from .terminal_notebook import TerminalNotebook


class MainWindow:
    """zzgShell 主窗口"""

    def __init__(self):
        # 使用 TkinterDnD 以支持拖放功能
        if DND_SUPPORT:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        self.root.title("zzgShell")
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)
        self.root.configure(bg='#f0f0f0')

        self._setup_ui()
        self._setup_menu()
        self._bind_shortcuts()

    def _setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg='#e0e0e0', height=70)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # Session 按钮
        session_btn = tk.Frame(toolbar, bg='#e0e0e0', cursor='hand2')
        session_btn.pack(side=tk.LEFT, padx=10, pady=5)

        icon_label = tk.Label(session_btn, text="🖥", bg='#e0e0e0', fg='#1976d2', font=('', 28))
        icon_label.pack()
        text_label = tk.Label(session_btn, text="Session", bg='#e0e0e0', fg='#333333', font=('', 10))
        text_label.pack()

        def on_click(e):
            self._on_add()
        def on_enter(e):
            session_btn.configure(bg='#d0d0d0')
            icon_label.configure(bg='#d0d0d0')
            text_label.configure(bg='#d0d0d0')
        def on_leave(e):
            session_btn.configure(bg='#e0e0e0')
            icon_label.configure(bg='#e0e0e0')
            text_label.configure(bg='#e0e0e0')

        for widget in (session_btn, icon_label, text_label):
            widget.bind('<Button-1>', on_click)
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪 - 点击 Session 添加连接")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg='#ffffff',
            fg='#333333',
            anchor=tk.W,
            padx=10,
            pady=5
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # 主区域容器 - 使用 PanedWindow 实现可拖动分隔线
        main_container = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            bg='#cccccc',
            sashwidth=4,
            sashrelief=tk.RAISED
        )
        main_container.pack(fill=tk.BOTH, expand=True)

        # 左侧面板
        left_frame = tk.Frame(main_container, bg='#ffffff', width=280)
        self.left_panel = LeftPanel(left_frame, self)
        self.left_panel.frame.pack(fill=tk.BOTH, expand=True)
        main_container.add(left_frame, minsize=200, width=280)

        # 右侧终端区域
        right_frame = tk.Frame(main_container, bg='#1e1e1e')
        self.terminal_notebook = TerminalNotebook(right_frame, self)
        self.terminal_notebook.frame.pack(fill=tk.BOTH, expand=True)
        main_container.add(right_frame, minsize=400)

    @property
    def connection_panel(self):
        return self.left_panel.connection_panel

    def update_sftp_panel(self, ssh_client):
        if ssh_client:
            self.left_panel.update_sftp(ssh_client)
        else:
            self.left_panel.disconnect_sftp()

    def _on_add(self):
        self.left_panel.connection_panel._on_add()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="添加连接", command=self._on_add, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")

    def _bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self._on_add())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def run(self):
        self.root.mainloop()
