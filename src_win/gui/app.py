"""GUI 应用入口 - Windows 版本"""

from src_win.gui.main_window import MainWindow


def run():
    """运行 GUI 应用"""
    app = MainWindow()
    app.run()
