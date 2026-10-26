# YTDownloader

English | **[简体中文](README.md)**

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的跨平台 YouTube 视频下载器（macOS / Windows）。ffmpeg、Deno、PO Token 全部内置，开箱即用。

## 设计理念 —— 粘贴，下载，完事

这个应用为**不想理解格式、编码、选项**的人而生：

- 粘贴链接，直接点下载。最佳格式**已自动选好**。
- 一切全内置：yt-dlp、ffmpeg、Deno、POT 支持。永远不需要额外安装任何东西。
- 出错时给你**人话指引**（换 VPN 节点 / 连手机热点 / 选浏览器读 Cookie），而不是一大段天书报错。
- 内置的 yt-dlp **自动自我更新** —— YouTube 例行改接口不需要重装应用。

## 功能

- MP4（H.264 + AAC）与 MKV（VP9/AV1 + Opus）输出，最高 4K / 60fps / HDR
- 内置 PO Token 支持（bgutil + Deno），高码率格式不再受限
- 浏览器 Cookie 支持：年龄限制 / 需登录视频（Chrome / Edge / Safari / Firefox / Brave 等）
- 中英双语界面，按系统语言自动适配，可手动切换
- 原生窗口（WKWebView / WebView2），下载完成后一键定位文件

## 安装

### macOS（推荐：一行命令）

在「终端」中粘贴执行：

```bash
curl -fsSL https://raw.githubusercontent.com/herrwelle/ytdownloader/main/install.sh | bash
```

自动识别 Apple Silicon / Intel、校验 SHA-256、安装到「应用程序」并清除隔离属性，**全程无 Gatekeeper 弹窗**。升级重跑一次即可。

手动安装：从 [Releases](https://github.com/herrwelle/ytdownloader/releases/latest) 下载 zip，解压后将 `YTDownloader.app` 拖入「应用程序」。首次打开若被拦截，右键 →「打开」，或到「系统设置 → 隐私与安全 → 仍要打开」。

### Windows

从 [Releases](https://github.com/herrwelle/ytdownloader/releases/latest) 下载：

- `YTDownloader-Setup.exe` — 安装版（推荐）
- `YTDownloader-Windows-Portable-*.zip` — 便携版，解压即用

浏览器下载如遇 SmartScreen 提示，点「更多信息 → 仍要运行」。

## 常见问题

**年龄限制视频？** 在「Cookie 来源」选择已登录 YouTube 的浏览器。macOS 的 Safari 需在系统设置授予应用「完全磁盘访问权限」；Chrome 首次可能弹钥匙串授权。Cookie 仅在本机读取，不上传。

**提示「Sign in to confirm you're not a bot」？** 你的 IP 被 YouTube 判定可疑（VPN/代理常见）。请更换 VPN 节点/地区——重连同一节点不会换 IP——或把电脑连到手机热点。

**macOS 提示「已损坏，无法打开」？** 用上面的终端一行命令安装（下载不带隔离标记）；或对已解压的 app 执行：
```bash
xattr -dr com.apple.quarantine /Applications/YTDownloader.app
```

## 从源码构建

macOS：

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller YTDownloader.spec
```

Windows 构建流程见 [`.github/workflows/build-windows.yml`](.github/workflows/build-windows.yml)（CI 自动出安装包）。

## 免责声明

本工具仅供个人学习、研究与备份自己的内容使用。请遵守 [YouTube 服务条款](https://www.youtube.com/t/terms) 及当地版权法律。

## 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) · [yt-dlp-ejs](https://pypi.org/project/yt-dlp-ejs/) — 下载核心与 JS 挑战求解器
- [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) · [Deno](https://deno.com/) — PO Token 生成
- [FFmpeg](https://ffmpeg.org/) · [pywebview](https://pywebview.flowrl.com/) · [FastAPI](https://fastapi.tiangolo.com/)
