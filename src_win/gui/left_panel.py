"""左侧面板 - Windows 优化版"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from src_win.gui.connection_panel import ConnectionPanel
from src_win.gui.sftp_panel import SFTPPanel
from src_win.storage import storage


class LeftPanel:
    """左侧面板 - Windows 优化"""

    # 配色
    BG_COLOR = '#ffffff'
    ICON_BAR_BG = '#f5f5f5'
    EXPORT_BG = '#fafafa'
    ACCENT_COLOR = '#0078d4'
    TEXT_COLOR = '#333333'
    MUTED_COLOR = '#888888'

    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = tk.Frame(parent, bg=self.BG_COLOR)

        self._current_tab = None
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        # 左侧图标栏
        self.icon_bar = tk.Frame(self.frame, bg=self.ICON_BAR_BG, width=48)
        self.icon_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.icon_bar.pack_propagate(False)

        # 右边框
        tk.Frame(self.icon_bar, bg='#e8e8e8', width=1).pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧容器
        self.right_container = tk.Frame(self.frame, bg=self.BG_COLOR)
        self.right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 连接列表区域
        self.content_width = 250
        self.content = tk.Frame(self.right_container, bg=self.BG_COLOR)

        # 列表分隔条
        self.list_sash = tk.Frame(self.right_container, bg='#e0e0e0', width=4, cursor='sb_h_double_arrow')
        self.list_sash.bind('<Enter>', lambda e: self.list_sash.configure(bg='#c0c0c0'))
        self.list_sash.bind('<Leave>', lambda e: self.list_sash.configure(bg='#e0e0e0'))

        # 导出区域
        self.export_area = tk.Frame(self.right_container, bg=self.EXPORT_BG)
        self._create_export_area()

        self._update_list_layout()
        self.list_sash.bind('<B1-Motion>', self._on_list_sash_drag)
        self.right_container.bind('<Configure>', lambda e: self._update_list_layout())

        # 创建面板
        self.connection_panel = ConnectionPanel(self.content, self.main_window)
        self.sftp_panel = SFTPPanel(self.content)

        # 创建图标按钮
        self._create_icon_buttons()
        self._show_connections()

    def _update_list_layout(self):
        """更新列表区域布局"""
        self.content.place(x=0, y=0, width=self.content_width, relheight=1)
        self.list_sash.place(x=self.content_width, y=0, width=4, relheight=1)
        self.export_area.place(x=self.content_width + 4, y=0, relwidth=1, relheight=1, width=-(self.content_width + 4))

    def _on_list_sash_drag(self, event):
        """拖动列表分隔条"""
        new_width = self.content_width + event.x
        new_width = max(160, min(new_width, 420))
        self.content_width = new_width
        self._update_list_layout()

    def _create_icon_buttons(self):
        """创建图标按钮"""
        self.star_btn = self._create_icon_button("☆", "连接", self._show_connections)
        self.star_btn.pack(pady=(16, 4))

        self.globe_btn = self._create_icon_button("⚫", "文件", self._show_sftp)
        self.globe_btn.pack(pady=4)

    def _create_icon_button(self, icon: str, tooltip: str, command):
        """创建图标按钮"""
        frame = tk.Frame(self.icon_bar, bg=self.ICON_BAR_BG)
        
        btn = tk.Label(
            frame,
            text=icon,
            bg=self.ICON_BAR_BG,
            fg=self.MUTED_COLOR,
            font=('Segoe UI', 16)
        )
        btn.pack()

        def on_click(e):
            command()
        def on_enter(e):
            if frame != self._current_tab:
                btn.configure(fg=self.TEXT_COLOR)
        def on_leave(e):
            if frame != self._current_tab:
                btn.configure(fg=self.MUTED_COLOR)

        frame.bind('<Button-1>', on_click)
        btn.bind('<Button-1>', on_click)
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        frame._btn = btn
        return frame

    def _update_tab_style(self, active_frame):
        """更新标签样式"""
        for frame in [self.star_btn, self.globe_btn]:
            frame._btn.configure(fg=self.MUTED_COLOR, bg=self.ICON_BAR_BG)
            frame.configure(bg=self.ICON_BAR_BG)

        active_frame._btn.configure(fg=self.ACCENT_COLOR, bg=self.BG_COLOR)
        active_frame.configure(bg=self.BG_COLOR)
        self._current_tab = active_frame

    def _show_connections(self):
        self._update_tab_style(self.star_btn)
        self.sftp_panel.frame.pack_forget()
        self.connection_panel.frame.pack(fill=tk.BOTH, expand=True)

    def _show_sftp(self):
        self._update_tab_style(self.globe_btn)
        self.connection_panel.frame.pack_forget()
        self.sftp_panel.frame.pack(fill=tk.BOTH, expand=True)

    def update_sftp(self, ssh_client):
        self.sftp_panel.set_client(ssh_client)
        self._show_sftp()

    def disconnect_sftp(self):
        self.sftp_panel.disconnect()

    def _create_export_area(self):
        """创建导出/导入区域"""
        # 居中容器
        center = tk.Frame(self.export_area, bg=self.EXPORT_BG)
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 按钮行
        btn_row = tk.Frame(center, bg=self.EXPORT_BG)
        btn_row.pack()

        # 导出按钮
        export_frame = tk.Frame(btn_row, bg=self.EXPORT_BG, padx=24, pady=16)
        export_frame.pack(side=tk.LEFT)

        export_icon = tk.Label(export_frame, text="↗", bg=self.EXPORT_BG, fg=self.ACCENT_COLOR, 
                               font=('Segoe UI', 28))
        export_icon.pack()
        export_text = tk.Label(export_frame, text="导出", bg=self.EXPORT_BG, fg=self.TEXT_COLOR,
                               font=('Segoe UI', 10))
        export_text.pack(pady=(6, 0))

        # 导入按钮
        import_frame = tk.Frame(btn_row, bg=self.EXPORT_BG, padx=24, pady=16)
        import_frame.pack(side=tk.LEFT)

        import_icon = tk.Label(import_frame, text="↙", bg=self.EXPORT_BG, fg='#107c10',
                               font=('Segoe UI', 28))
        import_icon.pack()
        import_text = tk.Label(import_frame, text="导入", bg=self.EXPORT_BG, fg=self.TEXT_COLOR,
                               font=('Segoe UI', 10))
        import_text.pack(pady=(6, 0))

        # 恢复布局
        reset_btn = tk.Label(center, text="◀ 恢复默认布局", bg=self.EXPORT_BG, fg=self.MUTED_COLOR,
                             font=('Segoe UI', 9))
        reset_btn.pack(pady=(32, 0))

        # 事件绑定
        def bind_hover(frame, icon, hover_bg='#f0f0f0'):
            def enter(e):
                frame.configure(bg=hover_bg)
                icon.configure(bg=hover_bg)
                for c in frame.winfo_children():
                    c.configure(bg=hover_bg)
            def leave(e):
                frame.configure(bg=self.EXPORT_BG)
                icon.configure(bg=self.EXPORT_BG)
                for c in frame.winfo_children():
                    c.configure(bg=self.EXPORT_BG)
            for w in [frame, icon] + list(frame.winfo_children()):
                w.bind('<Enter>', enter)
                w.bind('<Leave>', leave)

        bind_hover(export_frame, export_icon)
        bind_hover(import_frame, import_icon)

        for w in [export_frame, export_icon, export_text]:
            w.bind('<Button-1>', lambda e: self._on_export())
        for w in [import_frame, import_icon, import_text]:
            w.bind('<Button-1>', lambda e: self._on_import())
        reset_btn.bind('<Button-1>', lambda e: self.main_window.reset_layout())
        reset_btn.bind('<Enter>', lambda e: reset_btn.configure(fg=self.TEXT_COLOR))
        reset_btn.bind('<Leave>', lambda e: reset_btn.configure(fg=self.MUTED_COLOR))

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
                self.main_window.status_var.set(f"已导出 {count} 个连接")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))

    def _on_import(self):
        """导入连接"""
        file_path = filedialog.askopenfilename(
            title="导入连接",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                count = storage.import_connections(Path(file_path))
                self.main_window.status_var.set(f"已导入 {count} 个连接")
                self.connection_panel.refresh()
            except Exception as e:
                messagebox.showerror("导入失败", str(e))
