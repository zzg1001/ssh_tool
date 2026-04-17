"""主窗口 - Windows 优化版"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    from tkinterdnd2 import TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

from src_win.gui.left_panel import LeftPanel
from src_win.gui.terminal_notebook import TerminalNotebook
from src_win.storage import storage


class MainWindow:
    """zzgShell 主窗口 - Windows 优化"""

    # Windows 风格配色
    BG_COLOR = '#f3f3f3'
    TOOLBAR_BG = '#e8e8e8'
    ACCENT_COLOR = '#0078d4'
    TEXT_COLOR = '#1a1a1a'
    BORDER_COLOR = '#d1d1d1'

    def __init__(self):
        if DND_SUPPORT:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        
        self.root.title("zzgShell")
        self.root.geometry("1280x800")
        self.root.minsize(960, 640)
        self.root.configure(bg=self.BG_COLOR)

        # Windows 风格
        self._setup_style()
        self._setup_ui()
        self._setup_menu()
        self._bind_shortcuts()

    def _setup_style(self):
        """配置 ttk 样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置通用样式
        style.configure('TFrame', background=self.BG_COLOR)
        style.configure('TLabel', background=self.BG_COLOR, foreground=self.TEXT_COLOR, 
                       font=('Segoe UI', 9))
        style.configure('TButton', font=('Segoe UI', 9), padding=(12, 6))

    def _setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg=self.TOOLBAR_BG, height=64)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # 左侧分隔线
        tk.Frame(toolbar, bg=self.BORDER_COLOR, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        # Session 按钮
        session_frame = tk.Frame(toolbar, bg=self.TOOLBAR_BG)
        session_frame.pack(side=tk.LEFT, padx=12, pady=8)

        session_icon = tk.Label(
            session_frame, 
            text="＋", 
            bg=self.ACCENT_COLOR, 
            fg='white',
            font=('Segoe UI', 14, 'bold'),
            width=3, height=1,
            relief=tk.FLAT
        )
        session_icon.pack()
        
        session_text = tk.Label(
            session_frame, 
            text="新建连接", 
            bg=self.TOOLBAR_BG, 
            fg=self.TEXT_COLOR,
            font=('Segoe UI', 9)
        )
        session_text.pack(pady=(4, 0))

        def on_click(e):
            self._on_add()
        def on_enter(e):
            session_icon.configure(bg='#106ebe')
        def on_leave(e):
            session_icon.configure(bg=self.ACCENT_COLOR)

        for w in (session_frame, session_icon, session_text):
            w.bind('<Button-1>', on_click)
        session_icon.bind('<Enter>', on_enter)
        session_icon.bind('<Leave>', on_leave)

        # 标题
        title_label = tk.Label(
            toolbar,
            text="zzgShell",
            bg=self.TOOLBAR_BG,
            fg='#666666',
            font=('Segoe UI Semibold', 11)
        )
        title_label.pack(side=tk.RIGHT, padx=16)

        # 底部状态栏
        status_frame = tk.Frame(self.root, bg='#f8f8f8', height=26)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        tk.Frame(status_frame, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X, side=tk.TOP)
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg='#f8f8f8',
            fg='#666666',
            font=('Segoe UI', 8),
            anchor=tk.W,
            padx=12
        )
        status_label.pack(fill=tk.X, pady=4)

        # 主区域
        main_container = tk.Frame(self.root, bg=self.BG_COLOR)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 底层：左侧面板
        left_frame = tk.Frame(main_container, bg='#ffffff')
        left_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.left_panel = LeftPanel(left_frame, self)
        self.left_panel.frame.pack(fill=tk.BOTH, expand=True)

        # 上层：终端区域
        self.terminal_x = 300
        self.right_frame = tk.Frame(main_container, bg='#1e1e1e')
        
        # 左边框
        border_left = tk.Frame(self.right_frame, bg='#3c3c3c', width=1)
        border_left.pack(side=tk.LEFT, fill=tk.Y)
        
        terminal_inner = tk.Frame(self.right_frame, bg='#1e1e1e')
        terminal_inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.terminal_notebook = TerminalNotebook(terminal_inner, self)
        self.terminal_notebook.frame.pack(fill=tk.BOTH, expand=True)

        # 拖动条
        self.sash = tk.Frame(main_container, bg='#c0c0c0', width=5, cursor='sb_h_double_arrow')

        self._update_terminal_position()
        self.sash.bind('<B1-Motion>', self._on_sash_drag)
        self.sash.bind('<Enter>', lambda e: self.sash.configure(bg='#a0a0a0'))
        self.sash.bind('<Leave>', lambda e: self.sash.configure(bg='#c0c0c0'))
        main_container.bind('<Configure>', lambda e: self._update_terminal_position())

    def _update_terminal_position(self):
        """更新终端位置"""
        self.sash.place(x=self.terminal_x - 3, y=0, width=5, relheight=1)
        self.right_frame.place(x=self.terminal_x, y=0, relwidth=1, relheight=1, width=-self.terminal_x)

    def _on_sash_drag(self, event):
        """拖动分隔条"""
        new_x = self.sash.winfo_x() + event.x
        max_x = int(self.root.winfo_width() * 2 / 3)
        new_x = max(220, min(new_x, max_x))
        self.terminal_x = new_x
        self._update_terminal_position()

    def reset_layout(self):
        """恢复默认布局"""
        self.terminal_x = 300
        self._update_terminal_position()

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
        file_menu.add_command(label="导出连接", command=self._on_export, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")

    def _bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self._on_add())
        self.root.bind('<Control-e>', lambda e: self._on_export())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def _on_export(self):
        """导出连接"""
        connections = storage.list_connections()
        if not connections:
            messagebox.showinfo("提示", "没有可导出的连接")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出连接",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            initialfile="ssh_connections.json"
        )

        if file_path:
            try:
                count = storage.export_connections(Path(file_path), include_password=True)
                self.status_var.set(f"已导出 {count} 个连接")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))

    def run(self):
        self.root.mainloop()
