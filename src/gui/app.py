"""GUI 应用入口 - Tkinter 版本"""

import sys

from .main_window import MainWindow
from .security_guide import check_and_show_guide
from .installer import auto_eject_dmg


def run():
    """运行 GUI 应用"""
    if sys.platform == "darwin":
        # 如果从Applications启动且DMG还挂载，自动弹出
        auto_eject_dmg()

        # 首次运行安全设置
        if not check_and_show_guide():
            return

    app = MainWindow()
    app.run()
