"""
py2app 打包配置
使用方法: python setup.py py2app
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['paramiko', 'textual', 'cryptography', 'rich', 'src'],
    'includes': [
        'src.crypto',
        'src.storage',
        'src.ssh_client',
        'src.tui',
        'src.tui.app',
        'src.tui.connection_list',
        'src.tui.connection_form',
        'src.tui.terminal',
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
