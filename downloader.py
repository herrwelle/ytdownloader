import os
import shutil
import sys
import tempfile
import threading
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import yt_dlp

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

# 打包后内嵌的 ffmpeg 目录（PyInstaller --add-binary），开发时回退到 bin/ 或 PATH
_BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
# macOS .app：二进制在 Contents/Frameworks（_MEIPASS），数据文件在 Contents/Resources
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


def analyze(url):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'noprogress': True,
        'socket_timeout': 20,
    }
    _extractor_args_override(opts)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

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
                'sub': f'{ext} · 音画合一' + (f" · {int(f['fps'])}帧" if f.get('fps') and f['fps'] > 30 else ''),
                'size': size,
                'spec': str(f.get('format_id')),
                'mode': 'video',
            })
        elif vcodec != 'none':
            h = _height(f)
            if not h:
                continue
            fps = f.get('fps') or 0
            mark = ' (8K)' if h >= 4320 else ' (4K)' if h >= 2160 else ' (2K)' if h >= 1440 else ''
            codec = _codec_name(vcodec)
            video.append({
                'id': f.get('format_id'),
                'label': f'{h}p{mark}' + (f' · {int(fps)}帧' if fps > 30 else ''),
                'sub': f'{ext} · {codec} · 自动合并音轨',
                'size': size,
                'spec': f"{f.get('format_id')}+bestaudio/{f.get('format_id')}",
                'mode': 'video',
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
        'sub': '最佳音质自动转换 · 通用性最好',
        'size': None,
        'spec': 'bestaudio/bestaudio*',
        'mode': 'mp3',
    })

    return {
        'title': info.get('title') or '未知标题',
        'uploader': info.get('uploader') or info.get('channel') or '',
        'duration': duration,
        'thumbnail': info.get('thumbnail') or '',
        'webpage_url': info.get('webpage_url') or url,
        'progressive': progressive,
        'video': video,
        'audio': audio,
    }


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


def _download(task_id, url, spec, mode):
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
    }
    if FFMPEG_LOCATION:
        opts['ffmpeg_location'] = FFMPEG_LOCATION
    _extractor_args_override(opts)
    if mode == 'mp3':
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }]
    try:
        log(f'开始下载: {url} | 格式: {spec} | 模式: {mode} | ffmpeg: {FFMPEG_LOCATION or "PATH"} | deno: {DENO_DIR or "PATH"} | pot: {BGUTIL_SERVER_HOME or "无"} | yt-dlp: {yt_dlp.version.__version__}')
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as e:
            msg = str(e)
            if 'HTTP Error 403' in msg:
                # YouTube 风控拒绝当前客户端，换 tv 客户端重试（无需 PO token）
                log(f'403 被拒，改用 tv 客户端重试: {msg[:150]}')
                retry_opts = dict(opts)
                retry_args = dict(opts.get('extractor_args') or {})
                yt_args = dict(retry_args.get('youtube') or {})
                yt_args['player_client'] = ['tv']
                retry_args['youtube'] = yt_args
                retry_opts['extractor_args'] = retry_args
                with yt_dlp.YoutubeDL(retry_opts) as ydl:
                    ydl.download([url])
            elif mode == 'video' and 'Conversion failed' in msg:
                # 部分视频流含无时间戳数据包，mkv 封装器会失败；自动改用 mp4 容器重试（已下载的流会复用）
                log(f'mkv 合并失败，自动改用 mp4 容器重试: {msg[:150]}')
                retry_opts = dict(opts, merge_output_format='mp4')
                with yt_dlp.YoutubeDL(retry_opts) as ydl:
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
        task.update({'status': 'error', 'error': str(e)[:500]})
        log(f'失败: {type(e).__name__}: {e}\n{traceback.format_exc()}')
        shutil.rmtree(outdir, ignore_errors=True)


def start_download(url, spec, mode):
    task_id = uuid.uuid4().hex[:12]
    TASKS[task_id] = {'status': 'starting', 'progress': 0}
    threading.Thread(target=_download, args=(task_id, url, spec, mode), daemon=True).start()
    return task_id


def cleanup_task(task_id):
    task = TASKS.pop(task_id, None)
    if task and task.get('filepath'):
        shutil.rmtree(os.path.dirname(task['filepath']), ignore_errors=True)
