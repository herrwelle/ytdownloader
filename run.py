"""原生 app 入口：本地起 FastAPI 服务（后台线程）→ pywebview 原生窗口展示界面。"""
import os

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


def main():
    port = pick_port()
    server = uvicorn.Server(uvicorn.Config(
        fastapi_app, host='127.0.0.1', port=port, log_level='warning'))
    threading.Thread(target=server.run, daemon=True).start()

    import webview
    webview.create_window(
        'YTDownloader',
        f'http://127.0.0.1:{port}',
        width=880, height=680, min_size=(660, 540),
        background_color='#f5f5f7',
    )
    webview.start()


if __name__ == '__main__':
    main()
