#!/bin/bash
# yt-dlp 本地下载器 — 双击启动
cd "$(dirname "$0")" || exit 1
PORT=8765

echo "======================================"
echo "        yt-dlp 本地视频下载器"
echo "======================================"

# 检查 python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ 未找到 python3，请先安装："
    echo "   brew install python"
    read -r -p "按回车键关闭..." _
    exit 1
fi

# 已在运行则直接打开页面
if lsof -i ":$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "服务已在运行，直接打开页面..."
    open "http://localhost:$PORT"
    read -r -p "按回车键关闭..." _
    exit 0
fi

# 首次运行：创建虚拟环境并安装依赖
if [ ! -d ".venv" ]; then
    echo "首次运行：正在安装依赖（约 1-2 分钟，只需一次）..."
    python3 -m venv .venv || { echo "❌ 创建虚拟环境失败"; read -r -p "按回车键关闭..." _; exit 1; }
    ./.venv/bin/pip install --quiet --upgrade pip
    ./.venv/bin/pip install --quiet -r requirements.txt || {
        echo "❌ 依赖安装失败，请检查网络后重试"
        read -r -p "按回车键关闭..." _
        exit 1
    }
    echo "依赖安装完成。"
fi

# ffmpeg 检测（4K 合并 / MP3 转换需要）
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "⚠️  未检测到 ffmpeg：4K 视频合并和 MP3 转换将不可用"
    echo "   安装方法：brew install ffmpeg"
fi

echo ""
echo "启动服务中... 浏览器将自动打开 http://localhost:$PORT"
echo "关闭此 Terminal 窗口即停止服务"
echo ""

( sleep 1.5; open "http://localhost:$PORT" ) &
exec ./.venv/bin/uvicorn server:app --host 127.0.0.1 --port "$PORT"
