"""安装后自动弹出DMG"""

import os
import sys
import subprocess


def auto_eject_dmg():
    """如果从Applications启动且DMG还挂载着，自动弹出DMG"""
    if not getattr(sys, 'frozen', False):
        return

    # 检查是否从 Applications 运行
    app_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
    if not app_path.startswith("/Applications"):
        return

    # 检查 DMG 是否还挂载
    volume_path = "/Volumes/zzgShell"
    if os.path.exists(volume_path):
        # 弹出 DMG
        subprocess.Popen(
            ["hdiutil", "detach", volume_path, "-quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
