#!/bin/bash
set -euo pipefail

REPO="herrwelle/ytdownloader"
VERSION="v1.2.1"
APP_NAME="YTDownloader"

ARM_SHA="9ab67c215daead11fa0ceba00dcd3d6218e63cfa1012d4077a9400121cfb9c71"
INTEL_SHA="a7045d11d66b8910d8a7511dcc7819117a02e88931d13c0b42ac7f2a6e40f276"

if [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = "1" ]; then
    ARCH="arm64"
    ZIP="YTDownloader-mac-arm64.zip"
    SHA="$ARM_SHA"
else
    ARCH="x86_64"
    ZIP="YTDownloader-mac-intel-x86_64.zip"
    SHA="$INTEL_SHA"
fi

URL="https://github.com/${REPO}/releases/download/${VERSION}/${ZIP}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "下载 ${APP_NAME} ${VERSION} (macOS ${ARCH}) ..."
curl -fL --progress-bar -o "$TMP/$ZIP" "$URL"

echo "校验 SHA-256 ..."
echo "${SHA}  $TMP/$ZIP" | shasum -a 256 -c -

DEST="${YTD_INSTALL_DIR:-/Applications}"
mkdir -p "$DEST" 2>/dev/null || true
if [ ! -w "$DEST" ]; then
    DEST="$HOME/Applications"
    mkdir -p "$DEST"
fi

echo "安装到 ${DEST} ..."
rm -rf "${DEST}/${APP_NAME}.app"
ditto -x -k "$TMP/$ZIP" "$DEST"
xattr -dr com.apple.quarantine "${DEST}/${APP_NAME}.app" 2>/dev/null || true

echo ""
echo "完成！可从「启动台」打开 ${APP_NAME}，或运行："
echo "  open \"${DEST}/${APP_NAME}.app\""
