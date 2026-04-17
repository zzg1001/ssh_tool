"""添加/编辑连接对话框 - Windows 优化版"""

import uuid
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from src_win.storage import Connection


class ConnectionDialog:
    """连接编辑对话框 - Windows 风格"""

    # Windows 风格配色
    BG_COLOR = '#ffffff'
    HEADER_BG = '#f3f3f3'
    TEXT_COLOR = '#1a1a1a'
    LABEL_COLOR = '#666666'
    ACCENT_COLOR = '#0078d4'
    BORDER_COLOR = '#d1d1d1'
    INPUT_BG = '#ffffff'
    BTN_PRIMARY = '#0078d4'
    BTN_PRIMARY_HOVER = '#106ebe'
    BTN_CANCEL = '#e1e1e1'
    BTN_CANCEL_HOVER = '#c8c8c8'

    def __init__(self, parent, connection: Connection = None):
        self.result: Connection | None = None
        self.connection = connection
        self.is_edit = connection is not None

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑连接" if self.is_edit else "新建连接")
        self.dialog.geometry("420x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=self.BG_COLOR)

        self._setup_ui()

        if self.is_edit:
            self._load_connection()

        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def _setup_ui(self):
        """设置界面"""
        # 主容器
        main = tk.Frame(self.dialog, bg=self.BG_COLOR)
        main.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # 标题
        title = tk.Label(
            main,
            text="SSH 连接设置",
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            font=('Segoe UI Semibold', 14)
        )
        title.pack(anchor=tk.W, pady=(0, 16))

        # 表单区域
        form = tk.Frame(main, bg=self.BG_COLOR)
        form.pack(fill=tk.X)

        # Session Name
        self._create_label(form, "名称", 0)
        self.name_var = tk.StringVar()
        self.name_entry = self._create_entry(form, self.name_var, 0)

        # Host
        self._create_label(form, "主机 *", 1)
        self.host_var = tk.StringVar()
        self.host_entry = self._create_entry(form, self.host_var, 1)

        # Port
        self._create_label(form, "端口", 2)
        self.port_var = tk.StringVar(value="22")
        self.port_entry = self._create_entry(form, self.port_var, 2, width=10)

        # Username
        self._create_label(form, "用户名", 3)
        self.username_var = tk.StringVar()
        self.username_entry = self._create_entry(form, self.username_var, 3)

        # Password
        self._create_label(form, "密码", 4)
        self.password_var = tk.StringVar()
        self.password_entry = self._create_entry(form, self.password_var, 4, show="*")

        # Save password checkbox
        self.save_password_var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(
            form,
            text="保存密码",
            variable=self.save_password_var,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            activebackground=self.BG_COLOR,
            font=('Segoe UI', 9),
            selectcolor=self.BG_COLOR
        )
        cb.grid(row=5, column=1, sticky=tk.W, pady=(4, 8))

        # Private Key
        self._create_label(form, "私钥文件", 6)
        key_frame = tk.Frame(form, bg=self.BG_COLOR)
        key_frame.grid(row=6, column=1, sticky=tk.EW, pady=6)

        self.keyfile_var = tk.StringVar()
        self.keyfile_entry = tk.Entry(
            key_frame,
            textvariable=self.keyfile_var,
            font=('Segoe UI', 10),
            relief=tk.SOLID,
            bd=1,
            bg=self.INPUT_BG,
            fg=self.TEXT_COLOR
        )
        self.keyfile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = tk.Button(
            key_frame,
            text="浏览",
            command=self._browse_keyfile,
            font=('Segoe UI', 9),
            bg=self.BTN_CANCEL,
            fg=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=12
        )
        browse_btn.pack(side=tk.LEFT, padx=(8, 0))

        form.columnconfigure(1, weight=1)

        # 底部按钮
        self._setup_buttons(main)

    def _create_label(self, parent, text, row):
        """创建表单标签"""
        lbl = tk.Label(
            parent,
            text=text,
            bg=self.BG_COLOR,
            fg=self.LABEL_COLOR,
            font=('Segoe UI', 10),
            anchor=tk.E,
            width=10
        )
        lbl.grid(row=row, column=0, sticky=tk.E, pady=6, padx=(0, 12))

    def _create_entry(self, parent, var, row, width=None, show=None):
        """创建输入框"""
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=('Segoe UI', 10),
            relief=tk.SOLID,
            bd=1,
            bg=self.INPUT_BG,
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR
        )
        if show:
            entry.configure(show=show)
        if width:
            entry.configure(width=width)
            entry.grid(row=row, column=1, sticky=tk.W, pady=6)
        else:
            entry.grid(row=row, column=1, sticky=tk.EW, pady=6)
        return entry

    def _setup_buttons(self, parent):
        """设置底部按钮"""
        btn_frame = tk.Frame(parent, bg=self.BG_COLOR)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        # 取消按钮
        cancel_btn = tk.Label(
            btn_frame,
            text="取消",
            bg=self.BTN_CANCEL,
            fg=self.TEXT_COLOR,
            font=('Segoe UI', 10),
            padx=24,
            pady=8
        )
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.bind('<Button-1>', lambda e: self.dialog.destroy())
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.configure(bg=self.BTN_CANCEL_HOVER))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.configure(bg=self.BTN_CANCEL))

        # 确定按钮
        ok_btn = tk.Label(
            btn_frame,
            text="确定",
            bg=self.BTN_PRIMARY,
            fg='#ffffff',
            font=('Segoe UI', 10),
            padx=24,
            pady=8
        )
        ok_btn.pack(side=tk.RIGHT, padx=(0, 12))
        ok_btn.bind('<Button-1>', lambda e: self._on_save())
        ok_btn.bind('<Enter>', lambda e: ok_btn.configure(bg=self.BTN_PRIMARY_HOVER))
        ok_btn.bind('<Leave>', lambda e: ok_btn.configure(bg=self.BTN_PRIMARY))

    def _load_connection(self):
        """加载连接数据"""
        self.name_var.set(self.connection.name)
        self.host_var.set(self.connection.host)
        self.port_var.set(str(self.connection.port))
        self.username_var.set(self.connection.username)
        self.password_var.set(self.connection.password)
        self.save_password_var.set(bool(self.connection.password))
        self.keyfile_var.set(self.connection.key_file)

    def _browse_keyfile(self):
        """浏览密钥文件"""
        default_dir = str(Path.home() / ".ssh")
        filepath = filedialog.askopenfilename(
            initialdir=default_dir,
            title="选择私钥文件"
        )
        if filepath:
            self.keyfile_var.set(filepath)

    def _on_save(self):
        """保存"""
        name = self.name_var.get().strip()
        host = self.host_var.get().strip()
        username = self.username_var.get().strip()

        if not host:
            self.host_entry.focus_set()
            return

        if not name:
            name = f"{username}@{host}" if username else host

        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 22

        password = ""
        if self.save_password_var.get():
            password = self.password_var.get()

        self.result = Connection(
            id=self.connection.id if self.is_edit else str(uuid.uuid4()),
            name=name,
            host=host,
            port=port,
            username=username,
            password=password,
            key_file=self.keyfile_var.get().strip(),
        )
        self.dialog.destroy()
