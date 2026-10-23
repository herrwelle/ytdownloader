#!/bin/bash
set -euo pipefail

REPO="herrwelle/ytdownloader"
VERSION="v1.1.0"
APP_NAME="YTDownloader"

ARM_SHA="c5deb087fffaf5fb1b943a80e53ec5172507ea75fa4213cdd9d06ebcd53baf13"
INTEL_SHA="eb4803f79d2e002bce3b4fccf864fe414295f9173c04dd6ecec6eebf126764db"

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
