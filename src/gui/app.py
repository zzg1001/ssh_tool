"""GUI 应用入口 - Tkinter 版本"""

import sys
import os

from .main_window import MainWindow
from .security_guide import check_and_show_guide


def run():
    """运行 GUI 应用"""
    # macOS 下检查安全设置
    if sys.platform == "darwin":
        if not check_and_show_guide():
            # 用户取消了引导
            return

    app = MainWindow()
    app.run()
