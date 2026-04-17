"""添加/编辑连接对话框"""

import uuid
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from ..storage import Connection


class ConnectionDialog:
    """连接编辑对话框"""

    def __init__(self, parent, connection: Connection = None):
        self.result: Connection | None = None
        self.connection = connection
        self.is_edit = connection is not None

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Session Settings")
        self.dialog.geometry("450x380")
        self.dialog.resizable(True, True)
        self.dialog.minsize(400, 350)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='#ffffff')

        self._setup_buttons()  # 先创建按钮
        self._setup_ui()       # 再创建表单

        if self.is_edit:
            self._load_connection()

        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 380) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def _setup_ui(self):
        """设置界面"""
        # 主容器
        main = tk.Frame(self.dialog, bg='#ffffff', padx=25, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 标题
        title = tk.Label(main, text="🔐 SSH Connection", bg='#ffffff',
                        fg='#1976d2', font=('', 16, 'bold'))
        title.pack(anchor=tk.W, pady=(0, 20))

        # 表单区域
        form = tk.Frame(main, bg='#ffffff')
        form.pack(fill=tk.X)

        # Session Name
        self._create_field(form, "Session Name", 0)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(form, textvariable=self.name_var,
                                   font=('', 12), relief=tk.SOLID, bd=1)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        # Host
        self._create_field(form, "Host *", 1)
        self.host_var = tk.StringVar()
        self.host_entry = tk.Entry(form, textvariable=self.host_var,
                                   font=('', 12), relief=tk.SOLID, bd=1)
        self.host_entry.grid(row=1, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        # Port
        self._create_field(form, "Port", 2)
        self.port_var = tk.StringVar(value="22")
        self.port_entry = tk.Entry(form, textvariable=self.port_var,
                                   font=('', 12), relief=tk.SOLID, bd=1, width=8)
        self.port_entry.grid(row=2, column=1, sticky=tk.W, pady=8, padx=(10, 0))

        # Username
        self._create_field(form, "Username", 3)
        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(form, textvariable=self.username_var,
                                       font=('', 12), relief=tk.SOLID, bd=1)
        self.username_entry.grid(row=3, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        # Password
        self._create_field(form, "Password", 4)
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(form, textvariable=self.password_var,
                                       font=('', 12), relief=tk.SOLID, bd=1, show="●")
        self.password_entry.grid(row=4, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        # Save password checkbox
        self.save_password_var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(form, text="Remember password", variable=self.save_password_var,
                           bg='#ffffff', activebackground='#ffffff', font=('', 10))
        cb.grid(row=5, column=1, sticky=tk.W, pady=(0, 8), padx=(10, 0))

        # Private Key
        self._create_field(form, "Private Key", 6)
        key_frame = tk.Frame(form, bg='#ffffff')
        key_frame.grid(row=6, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        self.keyfile_var = tk.StringVar()
        self.keyfile_entry = tk.Entry(key_frame, textvariable=self.keyfile_var,
                                      font=('', 12), relief=tk.SOLID, bd=1)
        self.keyfile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = tk.Button(key_frame, text="...", command=self._browse_keyfile,
                              font=('', 10), width=3)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))

        form.columnconfigure(1, weight=1)

    def _setup_buttons(self):
        """设置底部按钮"""
        btn_frame = tk.Frame(self.dialog, bg='#f0f0f0', pady=15)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 按钮居中容器
        btn_inner = tk.Frame(btn_frame, bg='#f0f0f0')
        btn_inner.pack()

        # OK 按钮 (用 Label 模拟)
        ok_btn = tk.Label(btn_inner, text="    OK    ",
                         bg='#4caf50', fg='white',
                         font=('', 13, 'bold'),
                         padx=20, pady=10)
        ok_btn.pack(side=tk.LEFT, padx=10)
        ok_btn.bind('<Button-1>', lambda e: self._on_save())
        ok_btn.bind('<Enter>', lambda e: ok_btn.configure(bg='#45a049'))
        ok_btn.bind('<Leave>', lambda e: ok_btn.configure(bg='#4caf50'))

        # Cancel 按钮 (用 Label 模拟)
        cancel_btn = tk.Label(btn_inner, text="  Cancel  ",
                             bg='#f44336', fg='white',
                             font=('', 13, 'bold'),
                             padx=20, pady=10)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        cancel_btn.bind('<Button-1>', lambda e: self.dialog.destroy())
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.configure(bg='#e53935'))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.configure(bg='#f44336'))

    def _create_field(self, parent, label, row):
        """创建表单字段标签"""
        lbl = tk.Label(parent, text=label, bg='#ffffff', fg='#333333',
                      font=('', 11), anchor=tk.E, width=12)
        lbl.grid(row=row, column=0, sticky=tk.E, pady=8)

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
            title="Select Private Key"
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
