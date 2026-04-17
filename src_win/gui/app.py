"""GUI 应用入口 - Windows 版本"""

import ctypes
import sys

from src_win.gui.main_window import MainWindow


def _enable_dpi_awareness():
    """启用 Windows 高 DPI 感知，让界面更清晰"""
    if sys.platform == 'win32':
        try:
            # Windows 8.1+ Per-Monitor DPI Aware
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Windows Vista+ System DPI Aware
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def run():
    """运行 GUI 应用"""
    _enable_dpi_awareness()
    app = MainWindow()
    app.run()
