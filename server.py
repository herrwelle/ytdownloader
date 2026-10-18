import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.background import BackgroundTask

import downloader

BASE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))

app = FastAPI(title='yt-dlp 本地下载器')


class AnalyzeReq(BaseModel):
    url: str


class DownloadReq(BaseModel):
    url: str
    spec: str
    mode: str = 'video'


@app.post('/api/analyze')
def analyze(req: AnalyzeReq):
    url = req.url.strip()
    if not url:
        raise HTTPException(400, '请输入链接')
    try:
        return downloader.analyze(url)
    except Exception as e:
        msg = str(e)
        if 'Unsupported URL' in msg:
            msg = '不支持的链接，请检查后重试'
        raise HTTPException(400, msg)


@app.post('/api/download')
def download(req: DownloadReq):
    task_id = downloader.start_download(req.url.strip(), req.spec, req.mode)
    return {'task_id': task_id}


@app.get('/api/progress/{task_id}')
def progress(task_id: str):
    task = downloader.TASKS.get(task_id)
    if not task:
        raise HTTPException(404, '任务不存在')
    return task


@app.get('/api/file/{task_id}')
def file(task_id: str):
    task = downloader.TASKS.get(task_id)
    if not task or task.get('status') != 'done':
        raise HTTPException(404, '文件未就绪')
    return FileResponse(
        task['filepath'],
        filename=task['filename'],
        background=BackgroundTask(downloader.cleanup_task, task_id),
    )


@app.get('/api/reveal/{task_id}')
def reveal(task_id: str):
    task = downloader.TASKS.get(task_id)
    path = task and task.get('saved_path')
    if not path or not os.path.exists(path):
        raise HTTPException(404, '文件不存在')
    if sys.platform == 'darwin':
        subprocess.run(['open', '-R', path], check=False)
    elif os.name == 'nt':
        subprocess.run(['explorer', f'/select,{path}'], check=False)
    else:
        subprocess.run(['xdg-open', os.path.dirname(path)], check=False)
    return {'ok': True}


app.mount('/', StaticFiles(directory=BASE_DIR / 'static', html=True), name='static')
