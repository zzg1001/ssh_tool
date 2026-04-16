"""左侧面板 - 白色主题"""

import tkinter as tk

from .connection_panel import ConnectionPanel
from .sftp_panel import SFTPPanel


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

        # 内容区域
        self.content = tk.Frame(self.frame, bg='#ffffff')
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建面板
        self.connection_panel = ConnectionPanel(self.content, self.main_window)
        self.sftp_panel = SFTPPanel(self.content)

        # 创建图标按钮
        self._create_icon_buttons()

        # 默认显示连接列表
        self._show_connections()

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
