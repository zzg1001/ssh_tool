"""
Windows 打包脚本
使用方法：在 Windows 上运行 python build_win.py
"""

import PyInstaller.__main__
import shutil
import os
import sys

APP_NAME = "zzgShell"

# 清理旧文件
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)
if os.path.exists(f'{APP_NAME}.spec'):
    os.remove(f'{APP_NAME}.spec')

# PyInstaller 打包参数
PyInstaller.__main__.run([
    'main_win.py',
    '--name', APP_NAME,
    '--windowed',
    '--onefile',
    '--icon', 'zzgShell.ico',
    '--add-data', f'src_win{os.pathsep}src_win',
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
    '--noupx',
])

print(f"\n=== 完成 ===")
print(f"程序位置: dist/{APP_NAME}.exe")
