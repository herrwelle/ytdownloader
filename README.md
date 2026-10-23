# YTDownloader

跨平台 YouTube 视频下载器（macOS / Windows），基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp)。
内置 ffmpeg 与 Deno，无需额外配置即可下载最高画质（含需要 PO Token 的高码率格式）。

## 功能

- 支持 MP4（H.264 + AAC）与 MKV（VP9/AV1 + Opus）输出
- 自动获取最高画质，支持 4K / 60fps / HDR 源
- 支持读取浏览器 Cookie，可下载年龄限制 / 需登录的视频（Chrome / Edge / Safari / Firefox 等）
- 内置 POT（PO Token）支持，绕开 YouTube 对高画质格式的风控限制
- 原生桌面窗口（macOS WKWebView / Windows WebView2），深色模式
- 下载进度实时显示，完成后可在 Finder/资源管理器中定位文件
- ffmpeg、Deno、bgutil POT 服务全部随应用打包，开箱即用

## 安装

### macOS（推荐：一行命令）

在「终端」中粘贴执行：

```bash
curl -fsSL https://raw.githubusercontent.com/herrwelle/ytdownloader/main/install.sh | bash
```

脚本会自动识别 Apple Silicon / Intel，下载对应版本、校验 SHA-256、安装到「应用程序」，并清除隔离属性——**全程无 Gatekeeper 弹窗**。安装完成后从「启动台」打开即可。

> 也可以从 [Releases](https://github.com/herrwelle/ytdownloader/releases/latest) 手动下载 zip，解压后把 `YTDownloader.app` 拖入「应用程序」。首次打开若提示「无法验证开发者」，请右键 →「打开」，或到「系统设置 → 隐私与安全 → 仍要打开」。这是未公证应用的正常提示。

### Windows

从 [Releases](https://github.com/herrwelle/ytdownloader/releases/latest) 下载：

- `YTDownloader-Setup.exe` — 安装版（推荐）
- `YTDownloader-Windows-Portable-*.zip` — 便携版，解压即用

若浏览器下载后 SmartScreen 提示「Windows 已保护你的电脑」，点「更多信息 → 仍要运行」即可。

## 使用

1. 打开应用，粘贴 YouTube 视频链接
2. 选择格式（MP4 / MKV）与保存位置
3. 点击「下载」，完成后点击文件名可在文件夹中定位

## 常见问题

**提示「Sign in to confirm your age」（年龄限制视频）？**
在输入框下方「Cookie 来源」选择已登录 YouTube 的浏览器，然后重新分析、下载。注意：
- macOS Safari 需要先在「系统设置 → 隐私与安全性 → 完全磁盘访问权限」中允许本应用；
- Chrome 首次读取可能弹出钥匙串授权，选择「允许」；
- Cookie 仅在本机读取，不会上传到任何服务器。

**macOS 提示「已损坏，无法打开」？**
请使用上面的终端一行命令安装（下载过程不带隔离标记，不会触发 Gatekeeper）；或对已解压的 app 执行：
```bash
xattr -dr com.apple.quarantine /Applications/YTDownloader.app
```

**下载的不是最高画质？**
应用已内置 POT 支持；若仍受限，通常是源视频本身没有更高格式，或需要登录的内容（当前版本不支持登录）。

**支持其他网站吗？**
核心基于 yt-dlp，理论上支持其兼容的站点，但本项目仅针对 YouTube 做测试与适配。

## 从源码构建

macOS（PyInstaller）：

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller YTDownloader.spec
```

Windows 构建流程见 [`.github/workflows/build-windows.yml`](.github/workflows/build-windows.yml)（CI 自动出安装包）。

## 免责声明

本工具仅供个人学习、研究与备份自己的内容使用。请遵守 [YouTube 服务条款](https://www.youtube.com/t/terms) 及当地版权法律，勿用于商业用途或侵犯他人著作权。使用者需自行承担因使用本工具产生的一切责任。

## 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 下载核心
- [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) — PO Token 生成
- [Deno](https://deno.com/) — JS 运行时
- [FFmpeg](https://ffmpeg.org/) — 音视频合并
- [pywebview](https://pywebview.flowrl.com/) + [FastAPI](https://fastapi.tiangolo.com/) — 桌面界面与本地服务
