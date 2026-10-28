import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

# 跨平台日志文件：排查下载失败用
if sys.platform == 'darwin':
    LOG_FILE = Path.home() / 'Library' / 'Logs' / 'YTDownloader.log'
elif os.name == 'nt':
    LOG_FILE = Path.home() / 'AppData' / 'Local' / 'YTDownloader' / 'log.txt'
else:
    LOG_FILE = Path.home() / '.ytdownloader.log'


def log(line):
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 1024 * 1024:
            LOG_FILE.unlink()
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] {line}\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# yt-dlp 运行时自更新
# 用户数据目录中的新版 yt-dlp（及配套 ejs）优先于内置版本加载；
# 不改动 app 本体、不影响签名，损坏时自动回退内置版本。仅打包后启用。
# ---------------------------------------------------------------------------
if sys.platform == 'darwin':
    _DATA_HOME = Path.home() / 'Library' / 'Application Support' / 'YTDownloader'
elif os.name == 'nt':
    _DATA_HOME = Path.home() / 'AppData' / 'Local' / 'YTDownloader'
else:
    _DATA_HOME = Path.home() / '.local' / 'share' / 'YTDownloader'
UPDATE_DIR = _DATA_HOME / 'lib'
_FROZEN = bool(getattr(sys, 'frozen', False))


def _load_ytdlp():
    if _FROZEN and (UPDATE_DIR / 'yt_dlp').is_dir():
        sys.path.insert(0, str(UPDATE_DIR))
    try:
        import yt_dlp
    except Exception:
        if str(UPDATE_DIR) in sys.path:
            sys.path.remove(str(UPDATE_DIR))
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        log('自动更新的 yt-dlp 加载失败，已回退内置版本')
        import yt_dlp
    return yt_dlp


yt_dlp = _load_ytdlp()
from yt_dlp.postprocessor.ffmpeg import FFmpegVideoConvertorPP


def _ver_tuple(v):
    return tuple(int(x) for x in re.findall(r'\d+', v or '')[:3])


def _pypi(pkg):
    with urllib.request.urlopen(f'https://pypi.org/pypi/{pkg}/json', timeout=15) as r:
        data = json.load(r)
    return data['info']['version'], data['urls']


def check_update():
    """后台检查新版 yt-dlp 并下载到用户目录，下次启动生效（24 小时最多检查一次）。"""
    try:
        _DATA_HOME.mkdir(parents=True, exist_ok=True)
        marker = _DATA_HOME / 'lastcheck'
        if marker.exists() and time.time() - marker.stat().st_mtime < 86400:
            return
        marker.touch()
        cur = yt_dlp.version.__version__
        latest, wheels = _pypi('yt-dlp')
        if _ver_tuple(latest) <= _ver_tuple(cur):
            return
        dl = [(u['url'], u['filename']) for u in wheels
              if u['filename'].startswith('yt_dlp-') and u['filename'].endswith('-none-any.whl')]
        if not dl:
            return
        _, ejs_wheels = _pypi('yt-dlp-ejs')
        ejs_dl = [(u['url'], u['filename']) for u in ejs_wheels
                  if u['filename'].startswith('yt_dlp_ejs-') and u['filename'].endswith('-none-any.whl')]
        import zipfile
        staging = Path(tempfile.mkdtemp(prefix='ytd_update_')) / 'lib'
        staging.mkdir()
        for url, _fn in (dl + ejs_dl)[:2]:
            with urllib.request.urlopen(url, timeout=120) as r, tempfile.NamedTemporaryFile(delete=False) as f:
                shutil.copyfileobj(r, f)
                wheel = f.name
            with zipfile.ZipFile(wheel) as z:
                z.extractall(staging)
            os.unlink(wheel)
        new_dir = UPDATE_DIR.with_name('lib.new')
        shutil.rmtree(new_dir, ignore_errors=True)
        shutil.move(str(staging), str(new_dir))
        shutil.rmtree(UPDATE_DIR, ignore_errors=True)
        shutil.move(str(new_dir), str(UPDATE_DIR))
        log(f'yt-dlp 可更新: {cur} → {latest}（下次启动生效）')
    except Exception as e:
        log(f'yt-dlp 更新检查失败: {type(e).__name__}: {e}')


if _FROZEN:
    threading.Thread(target=check_update, daemon=True).start()

# 打包后内嵌的 ffmpeg 目录（PyInstaller --add-binary），开发时回退到 bin/ 或 PATH。
# PyInstaller 6 的 macOS .app 有两种布局：framework 包数据/二进制在 Contents/Frameworks
# （Resources 下是指向 Frameworks 的软链接）；非 framework 包 exe 在 Contents/MacOS 且
# _MEIPASS 指向 MacOS，但数据文件实际落在 Contents/Frameworks 与 Contents/Resources。
# 因此按 marker 探测各候选根，取第一个命中的目录。
def _data_root(marker):
    cands = [Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))]
    exe = Path(sys.executable).resolve()
    if exe.parent.name == 'MacOS':
        cands += [exe.parent.parent / 'Frameworks', exe.parent.parent / 'Resources']
    return next((d for d in cands if (d / marker).exists()), cands[0])

_BASE = _data_root('ffmpeg')
_APP_DATA = _BASE.parent / 'Resources'
_FFMPEG_CANDIDATES = [
    _BASE,
    Path(__file__).resolve().parent / 'bin',
]
FFMPEG_LOCATION = next(
    (str(d) for d in _FFMPEG_CANDIDATES
     if (d / 'ffmpeg').exists() or (d / 'ffmpeg.exe').exists()),
    None,
)

# JS runtime deno (required for obtaining YouTube HD formats; yt-dlp locates it via PATH) + PO token generation script directory (bgutil)
_DENO_CANDIDATES = [
    _BASE / 'deno',
    Path(__file__).resolve().parent / 'bin',
]
DENO_DIR = next(
    (str(d) for d in _DENO_CANDIDATES if (d / 'deno').exists() or (d / 'deno.exe').exists()),
    None,
)
if DENO_DIR:
    os.environ['PATH'] = DENO_DIR + os.pathsep + os.environ.get('PATH', '')
BGUTIL_SERVER_HOME = next(
    (str(d / 'bgutil/server') for d in (_BASE, _APP_DATA, Path(__file__).resolve().parent)
     if (d / 'bgutil/server/src/generate_once.ts').exists()),
    None,
)

def _extractor_args_override(opts):
    if BGUTIL_SERVER_HOME:
        opts.setdefault('extractor_args', {})['youtubepot-bgutilscript'] = {
            'server_home': [BGUTIL_SERVER_HOME],
        }


# bgutil 插件的脚本版本检查默认 15 秒；Windows 首次运行受 Defender 扫描影响易超时，
# 放宽到 120 秒。注意：必须等 yt-dlp 自身加载插件后再改属性——提前显式 import
# 插件模块会与 yt-dlp 的插件加载机制冲突（重复注册导致 POT 提供者不可用）。
_BGUTIL_PATCHED = False


def _patch_bgutil_timeout():
    global _BGUTIL_PATCHED
    if _BGUTIL_PATCHED:
        return
    mod = sys.modules.get('yt_dlp_plugins.extractor.getpot_bgutil_script')
    if mod is None:
        return
    try:
        mod.BgUtilScriptPTPBase._GET_SCRIPT_VSN_TIMEOUT = 120.0
        _BGUTIL_PATCHED = True
    except Exception:
        pass


def _warm_bgutil():
    if not (BGUTIL_SERVER_HOME and DENO_DIR):
        return
    deno = os.path.join(DENO_DIR, 'deno.exe' if os.name == 'nt' else 'deno')
    script = os.path.join(BGUTIL_SERVER_HOME, 'src', 'generate_once.ts')
    node_modules = os.path.join(BGUTIL_SERVER_HOME, 'node_modules')
    cache = os.path.join(os.path.expanduser('~'), '.cache', 'bgutil-ytdlp-pot-provider')
    try:
        r = subprocess.run(
            [deno, 'run', '--allow-env', '--allow-net',
             f'--allow-ffi={node_modules}', f'--allow-write={cache}',
             f'--allow-read={cache},{node_modules}', script, '--version'],
            capture_output=True, text=True, timeout=180,
        )
        log(f'POT 预热完成: rc={r.returncode} out={r.stdout.strip()[:60]}')
    except Exception as e:
        log(f'POT 预热失败: {type(e).__name__}: {e}')


if BGUTIL_SERVER_HOME and DENO_DIR:
    threading.Thread(target=_warm_bgutil, daemon=True).start()


COOKIE_BROWSERS = {'chrome', 'chromium', 'edge', 'firefox', 'safari', 'brave', 'opera', 'vivaldi', 'whale'}


def _apply_cookies(opts, cookies_from):
    if cookies_from in COOKIE_BROWSERS:
        opts['cookiesfrombrowser'] = (cookies_from, None, None, None)


def _is_cookie_lock_error(msg):
    return 'Could not copy' in msg and 'cookie database' in msg


_ERR = {
    'bot': {
        'zh': 'YouTube 风控拦截：当前网络 IP 被判定可疑。使用 VPN/代理的请更换节点（最好换地区，重连同一节点无效）；或将电脑连接到手机热点后重试；也可在「Cookie 来源」选择已登录 YouTube 的浏览器（Windows 需先完全退出该浏览器）',
        'en': 'YouTube risk-control block: your network IP looks suspicious. If you are using a VPN/proxy, switch to a different node/region (reconnecting to the same node will NOT change your IP); or connect your computer to a phone hotspot; or pick a browser logged into YouTube under "Cookie source" (on Windows, fully quit the browser first).',
    },
    'age': {
        'zh': '该视频有年龄限制：请在上方「Cookie 来源」选择已登录 YouTube 的浏览器后重试',
        'en': 'Age-restricted video: pick a browser logged into YouTube under "Cookie source" above and retry.',
    },
    'lock': {
        'zh': '无法读取浏览器 Cookie：浏览器正在运行，请完全退出（含后台进程）后重试；公开视频可切回「不使用」',
        'en': 'Cannot read browser cookies: the browser is running. Fully quit it (including background processes) and retry, or switch back to "None" for public videos.',
    },
    'unsupported': {
        'zh': '不支持的链接，请检查后重试',
        'en': 'Unsupported link, please check and retry.',
    },
    'bili': {
        'zh': 'B 站风控/区域限制：请在正常国内网络下重试，或在「Cookie 来源」选择已登录 B 站的浏览器（1080P 及以上需要登录）',
        'en': 'Bilibili risk-control / region restriction: retry on a normal network, or pick a browser logged into Bilibili under "Cookie source" (1080p+ requires login).',
    },
}


def _friendly_error(msg, lang='zh'):
    lang = lang if lang in ('zh', 'en') else 'zh'
    if 'not a bot' in msg:
        return _ERR['bot'][lang]
    if 'Sign in to confirm your age' in msg:
        return _ERR['age'][lang]
    if _is_cookie_lock_error(msg):
        return _ERR['lock'][lang]
    if 'Unsupported URL' in msg:
        return _ERR['unsupported'][lang]
    if 'Unable to extract initial state' in msg or ('geo-restricted' in msg and 'BiliBili' in msg):
        return _ERR['bili'][lang]
    return msg[:500]

# task_id -> {status, progress, speed, eta, filename, filepath, saved_path, error}
TASKS = {}

# 原生 app 模式：下载直接保存到「下载」文件夹，而非浏览器下载流
APP_NATIVE = os.environ.get('YTD_APP_MODE') == 'native'
DOWNLOADS_DIR = Path.home() / 'Downloads'


def _unique_dest(name):
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    base, ext = os.path.splitext(name)
    dest = DOWNLOADS_DIR / name
    i = 2
    while dest.exists():
        dest = DOWNLOADS_DIR / f'{base} ({i}){ext}'
        i += 1
    return dest


CODEC_NAMES = {
    'vp09': 'VP9', 'vp9': 'VP9', 'avc1': 'H.264', 'av01': 'AV1',
    'h264': 'H.264', 'mp4a': 'AAC', 'opus': 'OPUS', 'ec3': 'EAC3', 'ac4': 'AC4',
}


def _codec_name(c):
    base = (c or '').split('.')[0].lower()
    return CODEC_NAMES.get(base, base.upper())


def _fmt_size(f, duration):
    size = f.get('filesize') or f.get('filesize_approx')
    if size:
        return size
    tbr = f.get('tbr')
    if tbr and duration:
        return int(tbr * 1000 / 8 * duration)
    return None


def _height(f):
    h = f.get('height')
    return h or 0


_LOC = {
    'zh': {'av1': '音画合一', 'fps': '帧', 'merge': '自动合并音轨', 'mp3sub': '最佳音质自动转换 · 通用性最好', 'untitled': '未知标题'},
    'en': {'av1': 'audio + video in one', 'fps': ' fps', 'merge': 'audio auto-merged', 'mp3sub': 'Best quality, auto-converted', 'untitled': 'Untitled'},
}


def analyze(url, cookies_from=None, lang='zh'):
    t = _LOC[lang if lang in _LOC else 'zh']
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'noprogress': True,
        'socket_timeout': 20,
    }
    _apply_cookies(opts, cookies_from)
    _extractor_args_override(opts)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            _patch_bgutil_timeout()
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        # 浏览器锁定 Cookie 数据库时（Windows 常见），自动去掉 Cookie 重试一次
        if cookies_from and _is_cookie_lock_error(str(e)):
            log(f'Cookie 数据库被锁，自动回退无 Cookie 分析: {str(e)[:120]}')
            opts.pop('cookiesfrombrowser', None)
            with yt_dlp.YoutubeDL(opts) as ydl:
                _patch_bgutil_timeout()
                info = ydl.extract_info(url, download=False)
        else:
            raise

    duration = info.get('duration') or 0
    formats = info.get('formats') or []

    progressive, video, audio = [], [], []

    for f in formats:
        vcodec = f.get('vcodec') or 'none'
        acodec = f.get('acodec') or 'none'
        ext = f.get('ext') or ''
        size = _fmt_size(f, duration)

        if vcodec != 'none' and acodec != 'none':
            h = _height(f)
            if not h:
                continue
            progressive.append({
                'id': f.get('format_id'),
                'label': f'{h}p',
                'sub': f'{ext.upper()} · {t["av1"]}' + (f" · {int(f['fps'])}{t['fps']}" if f.get('fps') and f['fps'] > 30 else ''),
                'size': size,
                'spec': str(f.get('format_id')),
                'mode': 'video',
                'container': 'mp4',
            })
        elif vcodec != 'none':
            h = _height(f)
            if not h:
                continue
            fps = f.get('fps') or 0
            mark = ' (8K)' if h >= 4320 else ' (4K)' if h >= 2160 else ' (2K)' if h >= 1440 else ''
            codec = _codec_name(vcodec)
            container = 'mp4' if codec == 'H.264' else 'mkv'
            audio_spec = (
                f"{f.get('format_id')}+bestaudio[ext=m4a]/{f.get('format_id')}+bestaudio"
                if container == 'mp4'
                else f"{f.get('format_id')}+bestaudio"
            )
            video.append({
                'id': f.get('format_id'),
                'label': f'{h}p{mark}' + (f" · {int(fps)}{t['fps']}" if fps > 30 else ''),
                'sub': f'{"MP4" if container == "mp4" else "MKV"} · {codec} · {t["merge"]}',
                'size': size,
                'spec': f'{audio_spec}/{f.get("format_id")}',
                'mode': 'video',
                'container': container,
                '_h': h,
                '_fps': fps,
                '_ext': ext,
            })
        elif acodec != 'none':
            abr = f.get('abr')
            codec = _codec_name(acodec)
            audio.append({
                'id': f.get('format_id'),
                'label': f'{int(abr)} kbps' if abr else codec,
                'sub': f'{ext} · {codec}',
                'size': size,
                'spec': str(f.get('format_id')),
                'mode': 'audio',
                '_abr': abr or 0,
                '_ext': ext,
            })

    # 高清组去重：同分辨率+帧率 保留一种容器（mp4 优先）
    best = {}
    for f in video:
        key = (f['_h'], f['_fps'])
        if key not in best:
            best[key] = f
        else:
            cur = best[key]
            if (f['_ext'] == 'mp4') != (cur['_ext'] == 'mp4'):
                if f['_ext'] == 'mp4':
                    best[key] = f
    video = sorted(best.values(), key=lambda x: (-x['_h'], -x['_fps']))
    for f in video:
        f.pop('_h'), f.pop('_fps'), f.pop('_ext')

    progressive.sort(key=lambda x: int(''.join(c for c in x['label'] if c.isdigit()) or 0), reverse=True)

    # 音频去重：同容器保留最高码率一种
    audio.sort(key=lambda x: -x['_abr'])
    deduped, seen_ext = [], set()
    for f in audio:
        if f['_ext'] in seen_ext:
            continue
        seen_ext.add(f['_ext'])
        f.pop('_abr'), f.pop('_ext')
        deduped.append(f)
    audio = deduped

    # MP3 转换选项置顶
    audio.insert(0, {
        'id': 'mp3',
        'label': 'MP3',
        'sub': t['mp3sub'],
        'size': None,
        'spec': 'bestaudio/bestaudio*',
        'mode': 'mp3',
    })

    return {
        'title': info.get('title') or t['untitled'],
        'uploader': info.get('uploader') or info.get('channel') or '',
        'duration': duration,
        'thumbnail': info.get('thumbnail') or '',
        'webpage_url': info.get('webpage_url') or url,
        'progressive': progressive,
        'video': video,
        'audio': audio,
    }


def _pp_hook(task_id):
    def hook(d):
        if 'Convertor' not in (d.get('postprocessor') or ''):
            return
        task = TASKS.get(task_id)
        if not task:
            return
        if d['status'] == 'started':
            task['status'] = 'converting'
        elif d['status'] == 'finished' and task.get('status') == 'converting':
            task['status'] = 'processing'
    return hook


class _TranscodeMp4PP(FFmpegVideoConvertorPP):
    @staticmethod
    def _options(target_ext):
        yield from FFmpegVideoConvertorPP.stream_copy_opts(False)
        yield from ('-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                    '-c:a', 'aac', '-b:a', '192k', '-c:s', 'mov_text')


def _hook(task_id, d):
    task = TASKS.get(task_id)
    if not task:
        return
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes') or 0
        pct = round(downloaded / total * 100, 1) if total else 0
        task.update({
            'status': 'downloading',
            'progress': pct,
            'speed': d.get('speed'),
            'eta': d.get('eta'),
        })
    elif d['status'] == 'finished':
        task.update({'status': 'processing', 'progress': 100})


def _download(task_id, url, spec, mode, container=None, cookies_from=None, lang='zh'):
    task = TASKS[task_id]
    outdir = tempfile.mkdtemp(prefix='ytdl_')
    opts = {
        'format': spec,
        'outtmpl': os.path.join(outdir, '%(title).100s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'concurrent_fragment_downloads': 4,
        'progress_hooks': [lambda d: _hook(task_id, d)],
        'postprocessor_hooks': [_pp_hook(task_id)],
    }
    if container in ('mkv', 'transcode'):
        opts['merge_output_format'] = 'mkv'
    if FFMPEG_LOCATION:
        opts['ffmpeg_location'] = FFMPEG_LOCATION
    _apply_cookies(opts, cookies_from)
    _extractor_args_override(opts)
    if mode == 'mp3':
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }]
    def _open_ydl(o):
        ydl = yt_dlp.YoutubeDL(o)
        _patch_bgutil_timeout()
        if container == 'transcode':
            ydl.add_post_processor(_TranscodeMp4PP(preferedformat='mp4'))
        return ydl

    try:
        log(f'开始下载: {url} | 格式: {spec} | 模式: {mode} | 容器: {container or "默认"} | ffmpeg: {FFMPEG_LOCATION or "PATH"} | deno: {DENO_DIR or "PATH"} | pot: {BGUTIL_SERVER_HOME or "无"} | yt-dlp: {yt_dlp.version.__version__}')
        try:
            with _open_ydl(opts) as ydl:
                ydl.download([url])
        except Exception as e:
            msg = str(e)
            if cookies_from and _is_cookie_lock_error(msg):
                # 浏览器锁定 Cookie 数据库时（Windows 常见），自动去掉 Cookie 重试一次
                log(f'Cookie 数据库被锁，自动回退无 Cookie 下载: {msg[:120]}')
                fallback_opts = dict(opts)
                fallback_opts.pop('cookiesfrombrowser', None)
                with _open_ydl(fallback_opts) as ydl:
                    ydl.download([url])
            elif 'HTTP Error 403' in msg:
                # YouTube 风控拒绝当前客户端，换 tv 客户端重试（无需 PO token）
                log(f'403 被拒，改用 tv 客户端重试: {msg[:150]}')
                retry_opts = dict(opts)
                retry_args = dict(opts.get('extractor_args') or {})
                yt_args = dict(retry_args.get('youtube') or {})
                yt_args['player_client'] = ['tv']
                retry_args['youtube'] = yt_args
                retry_opts['extractor_args'] = retry_args
                with _open_ydl(retry_opts) as ydl:
                    ydl.download([url])
            elif mode == 'video' and 'Conversion failed' in msg:
                # 封装器拒绝该编码组合时换备用容器重试（已下载的流会复用）：默认 mp4 → 改试 mkv；mkv/transcode → 改试 mp4
                alt = 'mp4' if container in ('mkv', 'transcode') else 'mkv'
                log(f'合并失败，自动改用 {alt} 容器重试: {msg[:150]}')
                retry_opts = dict(opts, merge_output_format=alt)
                with _open_ydl(retry_opts) as ydl:
                    ydl.download([url])
            else:
                raise
        files = [x for x in os.listdir(outdir) if not x.startswith('.')]
        if not files:
            raise RuntimeError('下载完成但未找到输出文件')
        if APP_NATIVE:
            dest = _unique_dest(files[0])
            shutil.move(os.path.join(outdir, files[0]), dest)
            shutil.rmtree(outdir, ignore_errors=True)
            task.update({
                'status': 'done',
                'saved_path': str(dest),
                'filename': dest.name,
            })
        else:
            filepath = os.path.join(outdir, files[0])
            task.update({
                'status': 'done',
                'filepath': filepath,
                'filename': files[0],
            })
        log(f'成功: {task.get("filename")}')
    except Exception as e:
        task.update({'status': 'error', 'error': _friendly_error(str(e), lang)})
        log(f'失败: {type(e).__name__}: {e}\n{traceback.format_exc()}')
        shutil.rmtree(outdir, ignore_errors=True)


def start_download(url, spec, mode, container=None, cookies_from=None, lang='zh'):
    task_id = uuid.uuid4().hex[:12]
    TASKS[task_id] = {'status': 'starting', 'progress': 0}
    threading.Thread(
        target=_download,
        args=(task_id, url, spec, mode, container, cookies_from, lang),
        daemon=True,
    ).start()
    return task_id


def cleanup_task(task_id):
    task = TASKS.pop(task_id, None)
    if task and task.get('filepath'):
        shutil.rmtree(os.path.dirname(task['filepath']), ignore_errors=True)
