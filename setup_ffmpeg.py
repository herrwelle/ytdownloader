"""首次运行时自动下载 Windows 版 ffmpeg/ffprobe 到 bin/ 目录（只需一次）。"""
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BIN = Path(__file__).resolve().parent / 'bin'
URL = ('https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/'
       'ffmpeg-master-latest-win64-gpl.zip')


def main():
    if (BIN / 'ffmpeg.exe').exists():
        return
    print('正在下载 ffmpeg（约 100MB，只需一次）...')
    tmp = Path(tempfile.mkdtemp(prefix='ytdl_ffmpeg_'))
    archive = tmp / 'ffmpeg.zip'
    urllib.request.urlretrieve(URL, archive)
    print('正在解压...')
    BIN.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        wanted = [m for m in zf.namelist()
                  if m.endswith('ffmpeg.exe') or m.endswith('ffprobe.exe')]
        zf.extractall(tmp, members=wanted)
        for m in wanted:
            dest = BIN / Path(m).name
            if not dest.exists():
                shutil.move(tmp / m, dest)
    shutil.rmtree(tmp, ignore_errors=True)
    print('ffmpeg 就绪')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ffmpeg 下载失败: {e}')
        print('可手动下载 https://www.gyan.dev/ffmpeg/builds/ 并把 ffmpeg.exe、ffprobe.exe 放到 bin 文件夹')
        raise SystemExit(1)
