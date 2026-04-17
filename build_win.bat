@echo off
echo === zzgShell Windows 打包 ===
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：请先安装 Python
    pause
    exit /b 1
)

REM 安装依赖
echo 安装依赖...
pip install pyinstaller paramiko cryptography pyte

REM 运行打包脚本
echo 开始打包...
python build_win.py

echo.
echo === 完成 ===
pause
