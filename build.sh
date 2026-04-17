#!/bin/bash
# zzgShell 打包脚本

set -e

APP_NAME="zzgShell"
DIST_DIR="dist"
DMG_TMP="dist/dmg_tmp"

echo "=== 清理旧文件 ==="
rm -rf build "$DIST_DIR"

echo "=== 打包应用 ==="
python setup.py py2app

echo "=== 创建 DMG ==="
# 创建临时目录
mkdir -p "$DMG_TMP"
cp -R "$DIST_DIR/$APP_NAME.app" "$DMG_TMP/"
# 创建 Applications 快捷方式
ln -s /Applications "$DMG_TMP/Applications"

# 创建 DMG
hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_TMP" -ov -format UDZO "$DIST_DIR/$APP_NAME.dmg"

# 清理临时目录
rm -rf "$DMG_TMP"

echo "=== 完成 ==="
ls -lh "$DIST_DIR/$APP_NAME.dmg"
echo "DMG 位置: $DIST_DIR/$APP_NAME.dmg"
