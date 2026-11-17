#!/bin/bash
set -euo pipefail

REPO="herrwelle/ytdownloader"
VERSION="v1.2.2"
APP_NAME="YTDownloader"

ARM_SHA="b398caf99bb38fc2a76b3f46789f65c39e8107a1c8c29e0ed3907ed8f4746630"
INTEL_SHA="2b553684b81a078498f51ed563eab6285722b75c44a8bee5edc7e90c7cecb320"

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
