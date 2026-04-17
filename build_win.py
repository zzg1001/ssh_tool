"""
Windows 打包脚本
使用方法：在 Windows 上运行 python build_win.py
需要先安装：pip install pyinstaller
"""

import PyInstaller.__main__
import shutil
import os
import sys

APP_NAME = "zzgShell"

# 清理旧文件
for folder in ['build', 'dist', f'{APP_NAME}.spec']:
    if os.path.exists(folder):
        if os.path.isdir(folder):
            shutil.rmtree(folder)
        else:
            os.remove(folder)

# 获取 Python 路径
python_path = os.path.dirname(sys.executable)

# PyInstaller 打包参数
PyInstaller.__main__.run([
    'main.py',
    '--name', APP_NAME,
    '--windowed',  # 无控制台窗口
    '--onefile',   # 打包成单个 exe 文件
    '--icon', 'zzgShell.ico',
    '--add-data', f'src{os.pathsep}src',
    '--hidden-import', 'paramiko',
    '--hidden-import', 'cryptography',
    '--hidden-import', 'cffi',
    '--hidden-import', 'pyte',
    '--hidden-import', 'tkinter',
    '--hidden-import', 'bcrypt',
    '--hidden-import', 'nacl',
    '--collect-all', 'paramiko',
    '--collect-all', 'cryptography',
    '--collect-all', 'pyte',
    '--noupx',  # 不使用 UPX 压缩，避免兼容问题
])

print(f"\n=== 完成 ===")
print(f"程序位置: dist/{APP_NAME}.exe")
