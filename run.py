"""原生 app 入口：本地起 FastAPI 服务（后台线程）→ pywebview 原生窗口展示界面。"""
import io
import os
import sys

# Windows --windowed 模式下 stdout/stderr 为 None，uvicorn 日志初始化会崩溃
if sys.stdout is None:
    sys.stdout = io.open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None:
    sys.stderr = io.open(os.devnull, 'w', encoding='utf-8')

os.environ.setdefault('YTD_APP_MODE', 'native')

import socket
import threading

import uvicorn

from server import app as fastapi_app


def pick_port(start=8765):
    for p in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', p))
                return p
            except OSError:
                continue
    raise RuntimeError('没有可用端口')


class NativeApi:
    """暴露给 JS 的原生能力：读系统剪贴板（绕过 WKWebView 剪贴板权限限制）"""

    def read_clipboard(self):
        try:
            if sys.platform == 'darwin':
                from AppKit import NSPasteboard, NSPasteboardTypeString
                pb = NSPasteboard.generalPasteboard()
                return pb.stringForType_(NSPasteboardTypeString) or ''
            elif os.name == 'nt':
                import ctypes
                k32 = ctypes.windll.kernel32
                u32 = ctypes.windll.user32
                CF_UNICODETEXT = 13
                result = ''
                if k32.OpenClipboard(0):
                    try:
                        h = k32.GetClipboardData(CF_UNICODETEXT)
                        if h:
                            ptr = k32.GlobalLock(h)
                            if ptr:
                                result = ctypes.c_wchar_p(ptr).value or ''
                                k32.GlobalUnlock(h)
                    finally:
                        k32.CloseClipboard()
                return result
        except Exception:
            pass
        return ''


def main():
    port = pick_port()
    server = uvicorn.Server(uvicorn.Config(
        fastapi_app, host='127.0.0.1', port=port, log_level='warning', log_config=None))
    threading.Thread(target=server.run, daemon=True).start()

    import webview
    webview.create_window(
        'YTDownloader',
        f'http://127.0.0.1:{port}',
        width=880, height=680, min_size=(660, 540),
        background_color='#f5f5f7',
        js_api=NativeApi(),
    )
    webview.start()


if __name__ == '__main__':
    main()
