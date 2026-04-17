"""左侧连接列表面板 - Windows 优化版"""

import tkinter as tk
from tkinter import ttk, messagebox

from src_win.storage import storage, Connection
from src_win.gui.connection_dialog import ConnectionDialog


class ConnectionPanel:
    """连接列表面板 - Windows 风格"""

    # Windows 风格配色
    BG_COLOR = '#ffffff'
    HEADER_BG = '#f3f3f3'
    TEXT_COLOR = '#1a1a1a'
    ACCENT_COLOR = '#0078d4'
    SELECT_BG = '#cce4f7'
    BORDER_COLOR = '#e1e1e1'

    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = tk.Frame(parent, bg=self.BG_COLOR)

        self._connections: dict[str, Connection] = {}

        self._setup_ui()
        self._setup_context_menu()
        self.refresh()

    def _setup_ui(self):
        """设置界面"""
        # 标题栏
        header = tk.Frame(self.frame, bg=self.HEADER_BG, height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="  Sessions",
            bg=self.HEADER_BG,
            fg=self.TEXT_COLOR,
            font=('Segoe UI Semibold', 10),
            anchor=tk.W
        )
        title.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 分隔线
        tk.Frame(self.frame, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)

        # 列表容器
        list_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 连接列表 (使用 Listbox)
        self.listbox = tk.Listbox(
            list_frame,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            selectbackground=self.SELECT_BG,
            selectforeground=self.ACCENT_COLOR,
            font=('Segoe UI', 10),
            borderwidth=0,
            highlightthickness=0,
            activestyle='none',
            relief=tk.FLAT
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        # 绑定事件
        self.listbox.bind('<Double-1>', self._on_double_click)
        self.listbox.bind('<Return>', self._on_double_click)
        self.listbox.bind('<Button-2>', self._on_right_click)
        self.listbox.bind('<Button-3>', self._on_right_click)
        self.listbox.bind('<Control-Button-1>', self._on_right_click)

    def _setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = tk.Menu(
            self.frame,
            tearoff=0,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            activebackground=self.SELECT_BG,
            activeforeground=self.TEXT_COLOR,
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            bd=1
        )
        self.context_menu.add_command(label="连接", command=self._on_connect)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="编辑", command=self._on_edit)
        self.context_menu.add_command(label="删除", command=self._on_delete)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="断开当前连接", command=self._on_disconnect)

    def _on_right_click(self, event):
        """右键点击"""
        # 选中点击的项
        index = self.listbox.nearest(event.y)
        if index >= 0:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)

        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def refresh(self):
        """刷新连接列表"""
        self.listbox.delete(0, tk.END)
        self._connections.clear()

        connections = storage.list_connections()
        for conn in connections:
            self.listbox.insert(tk.END, f"  🖥  {conn.name}")
            self._connections[conn.name] = conn

    def get_selected(self) -> Connection | None:
        """获取选中的连接"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            # 从显示文本中提取名称
            text = self.listbox.get(index)
            name = text.replace("  🖥  ", "")
            return self._connections.get(name)
        return None

    def _on_double_click(self, event):
        """双击连接"""
        self._on_connect()

    def _on_connect(self):
        """连接"""
        conn = self.get_selected()
        if conn:
            self.main_window.terminal_notebook.open_connection(conn)
            self.main_window.status_var.set(f"正在连接: {conn.name}")

    def _on_add(self):
        """添加连接"""
        dialog = ConnectionDialog(self.main_window.root)
        if dialog.result:
            storage.add_connection(dialog.result)
            self.refresh()
            self.main_window.status_var.set(f"已添加: {dialog.result.name}")

    def _on_edit(self):
        """编辑连接"""
        conn = self.get_selected()
        if not conn:
            messagebox.showwarning("提示", "请先选择一个连接")
            return

        dialog = ConnectionDialog(self.main_window.root, conn)
        if dialog.result:
            storage.update_connection(dialog.result)
            self.refresh()
            self.main_window.status_var.set(f"已更新: {dialog.result.name}")

    def _on_delete(self):
        """删除连接"""
        conn = self.get_selected()
        if not conn:
            messagebox.showwarning("提示", "请先选择一个连接")
            return

        if messagebox.askyesno("确认删除", f"确定要删除连接 '{conn.name}' 吗？"):
            storage.delete_connection(conn.id)
            self.refresh()
            self.main_window.status_var.set(f"已删除: {conn.name}")

    def _on_disconnect(self):
        """断开当前连接"""
        self.main_window.terminal_notebook.close_current()
