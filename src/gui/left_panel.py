"""左侧面板 - 白色主题"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from .connection_panel import ConnectionPanel
from .sftp_panel import SFTPPanel
from ..storage import storage


class LeftPanel:
    """左侧面板"""

    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = tk.Frame(parent, bg='#ffffff')

        self._current_tab = None
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        # 左侧图标栏
        self.icon_bar = tk.Frame(self.frame, bg='#f5f5f5', width=45)
        self.icon_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.icon_bar.pack_propagate(False)

        # 右侧容器（用于放置可拖动的内容）
        self.right_container = tk.Frame(self.frame, bg='#ffffff')
        self.right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 连接列表区域
        self.content_width = 235
        self.content = tk.Frame(self.right_container, bg='#ffffff')

        # 列表分隔条
        self.list_sash = tk.Frame(self.right_container, bg='#e0e0e0', width=4, cursor='sb_h_double_arrow')

        # 右侧隐藏的导出区域
        self.export_area = tk.Frame(self.right_container, bg='#f5f5f5')
        self._create_export_button()

        # 使用 place 布局
        self._update_list_layout()

        # 绑定拖动事件
        self.list_sash.bind('<B1-Motion>', self._on_list_sash_drag)
        self.right_container.bind('<Configure>', lambda e: self._update_list_layout())

        # 创建面板
        self.connection_panel = ConnectionPanel(self.content, self.main_window)
        self.sftp_panel = SFTPPanel(self.content)

        # 创建图标按钮
        self._create_icon_buttons()

        # 默认显示连接列表
        self._show_connections()

    def _update_list_layout(self):
        """更新列表区域布局"""
        self.content.place(x=0, y=0, width=self.content_width, relheight=1)
        self.list_sash.place(x=self.content_width, y=0, width=4, relheight=1)
        self.export_area.place(x=self.content_width + 4, y=0, relwidth=1, relheight=1, width=-(self.content_width + 4))

    def _on_list_sash_drag(self, event):
        """拖动列表分隔条"""
        new_width = self.content_width + event.x
        # 限制范围：最小150，最大400
        new_width = max(150, min(new_width, 400))
        self.content_width = new_width
        self._update_list_layout()

    def _create_icon_buttons(self):
        """创建图标按钮"""
        self.star_btn = self._create_icon_button("⭐", self._show_connections)
        self.star_btn.pack(pady=(15, 5))

        self.globe_btn = self._create_icon_button("🌐", self._show_sftp)
        self.globe_btn.pack(pady=5)

    def _create_icon_button(self, icon: str, command):
        """创建图标按钮"""
        btn = tk.Label(
            self.icon_bar,
            text=icon,
            bg='#f5f5f5',
            font=('', 20)
        )

        def on_click(e):
            command()

        def on_enter(e):
            if btn != self._current_tab:
                btn.configure(bg='#e8e8e8')

        def on_leave(e):
            if btn != self._current_tab:
                btn.configure(bg='#f5f5f5')

        btn.bind('<Button-1>', on_click)
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

        return btn

    def _update_tab_style(self, active_btn):
        """更新标签样式"""
        for btn in [self.star_btn, self.globe_btn]:
            btn.configure(bg='#f5f5f5')

        active_btn.configure(bg='#ffffff')
        self._current_tab = active_btn

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

    def _create_export_button(self):
        """创建导出/导入按钮（居中显示）"""
        # 居中容器
        center_frame = tk.Frame(self.export_area, bg='#f5f5f5')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 按钮容器（横向排列）
        btn_row = tk.Frame(center_frame, bg='#f5f5f5')
        btn_row.pack()

        # 导出按钮
        export_frame = tk.Frame(btn_row, bg='#f5f5f5')
        export_frame.pack(side=tk.LEFT, padx=20)

        export_btn = tk.Label(export_frame, text="📤", bg='#f5f5f5', font=('', 36))
        export_btn.pack()
        export_label = tk.Label(export_frame, text="导出", bg='#f5f5f5', fg='#666666', font=('', 12))
        export_label.pack()

        # 导入按钮
        import_frame = tk.Frame(btn_row, bg='#f5f5f5')
        import_frame.pack(side=tk.LEFT, padx=20)

        import_btn = tk.Label(import_frame, text="📥", bg='#f5f5f5', font=('', 36))
        import_btn.pack()
        import_label = tk.Label(import_frame, text="导入", bg='#f5f5f5', fg='#666666', font=('', 12))
        import_label.pack()

        # 恢复布局按钮
        reset_btn = tk.Label(
            center_frame,
            text="◀ 恢复布局",
            bg='#f5f5f5',
            fg='#999999',
            font=('', 11),
                    )
        reset_btn.pack(pady=(30, 0))

        # 导出事件
        def on_export_click(e):
            self._on_export()
        def on_export_enter(e):
            export_frame.configure(bg='#e8e8e8')
            export_btn.configure(bg='#e8e8e8')
            export_label.configure(bg='#e8e8e8')
        def on_export_leave(e):
            export_frame.configure(bg='#f5f5f5')
            export_btn.configure(bg='#f5f5f5')
            export_label.configure(bg='#f5f5f5')

        # 导入事件
        def on_import_click(e):
            self._on_import()
        def on_import_enter(e):
            import_frame.configure(bg='#e8e8e8')
            import_btn.configure(bg='#e8e8e8')
            import_label.configure(bg='#e8e8e8')
        def on_import_leave(e):
            import_frame.configure(bg='#f5f5f5')
            import_btn.configure(bg='#f5f5f5')
            import_label.configure(bg='#f5f5f5')

        # 恢复布局事件
        def on_reset_click(e):
            self.main_window.reset_layout()
        def on_reset_enter(e):
            reset_btn.configure(fg='#666666')
        def on_reset_leave(e):
            reset_btn.configure(fg='#999999')

        for widget in (export_frame, export_btn, export_label):
            widget.bind('<Button-1>', on_export_click)
            widget.bind('<Enter>', on_export_enter)
            widget.bind('<Leave>', on_export_leave)

        for widget in (import_frame, import_btn, import_label):
            widget.bind('<Button-1>', on_import_click)
            widget.bind('<Enter>', on_import_enter)
            widget.bind('<Leave>', on_import_leave)

        reset_btn.bind('<Button-1>', on_reset_click)
        reset_btn.bind('<Enter>', on_reset_enter)
        reset_btn.bind('<Leave>', on_reset_leave)

    def _on_export(self):
        """导出所有连接"""
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
                messagebox.showerror("导出失败", f"导出时发生错误：{e}")

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
                # 刷新连接列表
                self.connection_panel.refresh()
            except Exception as e:
                messagebox.showerror("导入失败", f"导入时发生错误：{e}")
