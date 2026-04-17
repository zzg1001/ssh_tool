"""主窗口 - 白色主题"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

try:
    from tkinterdnd2 import TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

from .left_panel import LeftPanel
from .terminal_notebook import TerminalNotebook
from ..storage import storage


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
        session_btn = tk.Frame(toolbar, bg='#e0e0e0', )
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

        # 主区域容器
        main_container = tk.Frame(self.root, bg='#ffffff')
        main_container.pack(fill=tk.BOTH, expand=True)

        # 底层：左侧面板（铺满整个区域）
        left_frame = tk.Frame(main_container, bg='#ffffff')
        left_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.left_panel = LeftPanel(left_frame, self)
        self.left_panel.frame.pack(fill=tk.BOTH, expand=True)

        # 上层：终端区域（可拖动左边界）
        self.terminal_x = 280  # 终端左边界初始位置
        self.right_frame = tk.Frame(main_container, bg='#1e1e1e', highlightthickness=2, highlightbackground='#444444')
        self.terminal_notebook = TerminalNotebook(self.right_frame, self)
        self.terminal_notebook.frame.pack(fill=tk.BOTH, expand=True)

        # 拖动条
        self.sash = tk.Frame(main_container, bg='#666666', width=6, cursor='sb_h_double_arrow')

        # 初始布局
        self._update_terminal_position()

        # 绑定拖动事件
        self.sash.bind('<B1-Motion>', self._on_sash_drag)
        main_container.bind('<Configure>', lambda e: self._update_terminal_position())

    def _update_terminal_position(self):
        """更新终端位置"""
        self.sash.place(x=self.terminal_x - 2, y=0, width=4, relheight=1)
        self.right_frame.place(x=self.terminal_x, y=0, relwidth=1, relheight=1, width=-self.terminal_x)

    def _on_sash_drag(self, event):
        """拖动分隔条"""
        new_x = self.sash.winfo_x() + event.x
        # 限制范围：最小200，最大屏幕2/3
        max_x = int(self.root.winfo_width() * 2 / 3)
        new_x = max(200, min(new_x, max_x))
        self.terminal_x = new_x
        self._update_terminal_position()

    def reset_layout(self):
        """恢复默认布局"""
        self.terminal_x = 280
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
        file_menu.add_command(label="导出所有连接", command=self._on_export, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")

    def _bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self._on_add())
        self.root.bind('<Control-e>', lambda e: self._on_export())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def _on_export(self):
        """导出所有连接（含明文密码）"""
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
                messagebox.showerror("导出失败", f"导出时发生错误：{e}")

    def run(self):
        self.root.mainloop()
