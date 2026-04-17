"""
Windows 打包脚本
使用方法：在 Windows 上运行 python build_win.py
需要先安装：pip install pyinstaller
"""

import PyInstaller.__main__
import shutil
import os

APP_NAME = "zzgShell"

# 清理旧文件
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# PyInstaller 打包参数
PyInstaller.__main__.run([
    'main.py',
    '--name', APP_NAME,
    '--windowed',  # 无控制台窗口
    '--onedir',    # 打包成文件夹
    '--icon', 'zzgShell.ico',  # 需要准备 .ico 图标
    '--add-data', 'src;src',
    '--hidden-import', 'paramiko',
    '--hidden-import', 'cryptography',
    '--hidden-import', 'cffi',
    '--hidden-import', 'pyte',
    '--hidden-import', 'tkinter',
    '--collect-all', 'paramiko',
    '--collect-all', 'cryptography',
])

print(f"\n=== 完成 ===")
print(f"程序位置: dist/{APP_NAME}/{APP_NAME}.exe")
