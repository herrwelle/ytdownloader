#!/bin/bash
set -euo pipefail

REPO="herrwelle/ytdownloader"
VERSION="v1.1.3"
APP_NAME="YTDownloader"

ARM_SHA="feedec1808cda3bfa56e15a9b475e811ecc80731c71139dfe5aaee5810a6f4a0"
INTEL_SHA="141e37a747c85fbad7be5d11c97c4eacf836a210d47d8d0e850c81708c6f482e"

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
