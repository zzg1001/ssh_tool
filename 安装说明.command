#!/bin/bash
# SSH Tool 安装引导
# 双击此文件来完成安全设置

clear

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              SSH Tool 安装引导                               ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  由于 macOS 的安全机制，首次运行需要进行以下设置。"
echo "  这是一次性操作，完成后即可正常使用。"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="$SCRIPT_DIR/SSH Tool.app"

# 检查应用是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "  [错误] 未找到 SSH Tool.app"
    echo "  请确保此脚本与 SSH Tool.app 在同一目录下。"
    echo ""
    echo "  按任意键退出..."
    read -n 1
    exit 1
fi

echo "  [1/3] 正在移除安全隔离属性..."
xattr -cr "$APP_PATH" 2>/dev/null
echo "        ✓ 完成"
echo ""

echo "  [2/3] 正在设置执行权限..."
chmod +x "$APP_PATH/Contents/MacOS/launch" 2>/dev/null
echo "        ✓ 完成"
echo ""

echo "  [3/3] 正在验证..."
if [ -x "$APP_PATH/Contents/MacOS/launch" ]; then
    echo "        ✓ 验证通过"
else
    echo "        [警告] 验证失败，可能需要手动设置权限"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ 安装完成！"
echo ""
echo "  现在您可以双击 SSH Tool.app 来启动应用了。"
echo ""
echo "  如果仍然出现安全提示，请尝试："
echo "  1. 右键点击 SSH Tool.app"
echo "  2. 选择「打开」"
echo "  3. 在弹出的对话框中点击「打开」"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 询问是否立即打开应用
echo "  是否立即打开 SSH Tool？(Y/n)"
read -n 1 -r REPLY
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "  正在启动 SSH Tool..."
    open "$APP_PATH"
fi

echo ""
echo "  按任意键关闭此窗口..."
read -n 1
