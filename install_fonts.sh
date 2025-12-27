#!/bin/bash
# install_fonts.sh - 安裝支援臺灣客語（擴展漢字）的字體
#
# 臺灣客語使用的漢字有些在 CJK 擴展區（Extension B/C/D/E/F），
# 一般字體不支援這些字符，會顯示為方塊（豆腐字）。
# 此腳本安裝花園明朝字體，支援最廣泛的 Unicode 漢字。

set -e

echo "================================================"
echo "安裝擴展漢字字體（花園明朝）"
echo "================================================"
echo ""

# 檢查是否已安裝
if [ -f "$HOME/Library/Fonts/HanaMinA.otf" ]; then
    echo "✓ 花園明朝字體已安裝"
    echo ""
    echo "如需重新安裝，請先刪除字體："
    echo "  rm ~/Library/Fonts/HanaMin*.otf"
    exit 0
fi

echo "下載花園明朝字體..."
cd /tmp
curl -L --progress-bar -o HanaMin.zip \
    "https://github.com/cjkvi/HanaMinAFDKO/releases/download/2021-01-18/HanaMin-AFDKO-2021-01-18.zip"

echo ""
echo "解壓縮..."
unzip -o -q HanaMin.zip

echo "安裝字體到 ~/Library/Fonts/ ..."
cp HanaMin-AFDKO-2021-01-18/*.otf ~/Library/Fonts/

echo "清理暫存檔..."
rm -rf HanaMin-AFDKO-2021-01-18*
rm -f HanaMin.zip

echo ""
echo "================================================"
echo "✓ 安裝完成！"
echo "================================================"
echo ""
echo "後續設定："
echo ""
echo "1. 終端機字體設定："
echo "   • iTerm2: Preferences → Profiles → Text → Font"
echo "   • Terminal.app: 偏好設定 → 描述檔 → 字體"
echo "   選擇 'HanaMinA' 或勾選 Non-ASCII Font"
echo ""
echo "2. 字幕視窗字體設定："
echo "   編輯 subtitle/subtitle.py，修改 FONT_NAME："
echo "   FONT_NAME = \"HanaMinA\""
echo ""
echo "3. 重新啟動終端機和應用程式以套用新字體"
echo ""
