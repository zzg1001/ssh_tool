"""
py2app 打包配置
使用方法: python setup.py py2app
"""

import sys
from pathlib import Path
from setuptools import setup

# 动态查找 Python 库目录
python_lib = Path(sys.prefix) / 'lib'

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'zzgShell.icns',
    'frameworks': [
        str(python_lib / 'libffi.8.dylib'),
        str(python_lib / 'libtk8.6.dylib'),
        str(python_lib / 'libtcl8.6.dylib'),
        str(python_lib / 'libssl.3.dylib'),
        str(python_lib / 'libcrypto.3.dylib'),
    ],
    'packages': ['paramiko', 'cryptography', 'cffi', 'pyte', 'src'],
    'includes': [
        'src.crypto',
        'src.storage',
        'src.ssh_client',
        'src.gui',
        'src.gui.app',
        'src.gui.main_window',
        'src.gui.left_panel',
        'src.gui.connection_panel',
        'src.gui.connection_dialog',
        'src.gui.terminal_notebook',
        'src.gui.terminal_widget',
        'src.gui.terminal_tabs',
        'src.gui.sftp_panel',
        'src.gui.installer',
        'src.gui.security_guide',
    ],
    'plist': {
        'CFBundleName': 'zzgShell',
        'CFBundleDisplayName': 'zzgShell',
        'CFBundleIdentifier': 'com.zzg.shell',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
    },
}

setup(
    name='zzgShell',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
