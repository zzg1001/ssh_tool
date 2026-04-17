"""终端标签页管理"""

from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from src_win.gui.terminal_widget import TerminalWidget
from src_win.storage import Connection


class TerminalTabs(QTabWidget):
    """终端标签页"""

    def __init__(self):
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self._on_tab_close)

        self.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
        """)

        # 显示欢迎页
        self._show_welcome()

    def _show_welcome(self):
        """显示欢迎页"""
        welcome = QWidget()
        layout = QVBoxLayout(welcome)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("双击左侧连接开始 SSH 会话")
        label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 16px;
            }
        """)
        layout.addWidget(label)

        self.addTab(welcome, "欢迎")

    def open_connection(self, conn: Connection):
        """打开新连接"""
        # 移除欢迎页
        if self.count() == 1 and self.tabText(0) == "欢迎":
            self.removeTab(0)

        # 创建终端
        terminal = TerminalWidget(conn)
        index = self.addTab(terminal, conn.name)
        self.setCurrentIndex(index)

        # 开始连接
        terminal.start_connection()

    def close_current_tab(self):
        """关闭当前标签"""
        index = self.currentIndex()
        if index >= 0:
            self._on_tab_close(index)

    def _on_tab_close(self, index: int):
        """关闭标签页"""
        widget = self.widget(index)
        if isinstance(widget, TerminalWidget):
            widget.disconnect_ssh()
        self.removeTab(index)

        # 如果没有标签了，显示欢迎页
        if self.count() == 0:
            self._show_welcome()
