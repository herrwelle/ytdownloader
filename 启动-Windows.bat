@echo off
chcp 65001 >nul
cd /d "%~dp0"
title YTDownloader

rem ---- 找 Python ----
set PY=
where py >nul 2>nul && set PY=py -3
if "%PY%"=="" where python >nul 2>nul && set PY=python
if "%PY%"=="" (
    echo 未找到 Python，尝试自动安装（需要网络，装完请重新双击本文件）...
    winget install -e --id Python.Python.3.13 --silent --accept-source-agreements --accept-package-agreements
    echo.
    echo 如果上方显示安装成功，请重新双击 启动.bat
    pause
    exit /b 1
)

rem ---- 首次运行：虚拟环境 + 依赖 ----
if not exist .venv (
    echo 首次运行：正在安装依赖（约 1-2 分钟，只需一次）...
    %PY% -m venv .venv || (echo 创建虚拟环境失败 & pause & exit /b 1)
    .venv\Scripts\pip install --quiet --upgrade pip
    .venv\Scripts\pip install --quiet -r requirements.txt || (echo 依赖安装失败，请检查网络 & pause & exit /b 1)
)

rem ---- 首次运行：下载 ffmpeg ----
if not exist bin\ffmpeg.exe (
    .venv\Scripts\python setup_ffmpeg.py || (pause & exit /b 1)
)

rem ---- 启动（pythonw 无控制台窗口）----
start "" .venv\Scripts\pythonw.exe run.py
exit
