# YTDownloader

**[简体中文](README.zh-CN.md)** | English

A cross-platform YouTube video downloader (macOS / Windows) built on [yt-dlp](https://github.com/yt-dlp/yt-dlp). ffmpeg, Deno and the PO Token provider are all bundled — it just works.

## Philosophy — Paste. Download. Done.

This app is built for people who **don't want to understand formats, codecs or options**:

- Paste a link, press Download. The best format is **pre-selected automatically**.
- Everything is bundled: yt-dlp, ffmpeg, Deno, POT support. No extra installs, ever.
- When something goes wrong, you get **plain-language guidance** (switch VPN node / use a phone hotspot / pick a browser for cookies) — not a wall of error code.
- The bundled yt-dlp **updates itself automatically** — routine YouTube changes never require reinstalling the app.

## Features

- MP4 (H.264 + AAC) and MKV (VP9/AV1 + Opus) output, up to 4K/60fps/HDR
- Built-in PO Token support (bgutil + Deno) for high-bitrate formats
- Browser cookie support for age-restricted / login-required videos (Chrome / Edge / Safari / Firefox / Brave / …)
- Bilingual UI (中文 / English), auto-detected from your system
- Native window (WKWebView / WebView2), one-click reveal of finished files

## Install

### macOS (one line)

Paste this into **Terminal**:

```bash
curl -fsSL https://raw.githubusercontent.com/herrwelle/ytdownloader/main/install.sh | bash
```

Detects Apple Silicon / Intel automatically, verifies SHA-256, installs to `/Applications` and clears the quarantine flag — **no Gatekeeper popup**. Re-run to update.

Manual: download the zip from [Releases](https://github.com/herrwelle/ytdownloader/releases/latest), unzip, drag `YTDownloader.app` to Applications. If macOS blocks it (unsigned app), right-click → Open, or allow it in System Settings → Privacy & Security.

### Windows

From [Releases](https://github.com/herrwelle/ytdownloader/releases/latest):

- `YTDownloader-Setup.exe` — installer (recommended)
- `YTDownloader-Windows-Portable-*.zip` — portable, unzip and run

If SmartScreen warns, click "More info → Run anyway".

## FAQ

**Age-restricted video?** Pick a browser that is logged into YouTube under "Cookie source". On macOS, Safari needs Full Disk Access granted to the app; Chrome may ask for Keychain access once. Cookies are read locally only.

**"Sign in to confirm you're not a bot"?** Your IP looks suspicious to YouTube (common with VPN/proxy). Switch to a different VPN node/region — reconnecting to the *same* node does not change your IP — or connect your computer to a phone hotspot.

**"Damaged and can't be opened" on macOS?** Use the one-line installer above (no quarantine flag), or run:
```bash
xattr -dr com.apple.quarantine /Applications/YTDownloader.app
```

## Build from source

macOS:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller YTDownloader.spec
```

Windows CI: see [`.github/workflows/build-windows.yml`](.github/workflows/build-windows.yml).

## Disclaimer

For personal learning, research and backing up your own content only. Please respect the [YouTube Terms of Service](https://www.youtube.com/t/terms) and copyright law in your jurisdiction.

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) · [yt-dlp-ejs](https://pypi.org/project/yt-dlp-ejs/) — download core & JS challenge solver
- [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) · [Deno](https://deno.com/) — PO Token generation
- [FFmpeg](https://ffmpeg.org/) · [pywebview](https://pywebview.flowrl.com/) · [FastAPI](https://fastapi.tiangolo.com/)
