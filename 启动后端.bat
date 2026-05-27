@echo off
chcp 65001 >nul
title 法律案件追踪系统 - 后端服务

cd /d "%~dp0"

echo ================================================
echo        法律案件追踪系统 - 后端服务启动器
echo ================================================
echo.

:: 检查 Python
set PYTHON_PATH=C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe
"%PYTHON_PATH%" --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [OK] Python 已找到
echo.

:: 检查端口是否被占用
netstat -ano | findstr ":8002 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 8002 已被占用，正在关闭旧进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002 " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 >nul
    echo [OK] 旧进程已关闭
    echo.
)

:: 检查依赖
echo [检查] 正在检查依赖...
"%PYTHON_PATH%" -c "import fastapi, sqlalchemy, dashscope" 2>nul
if errorlevel 1 (
    echo [警告] 缺少依赖，正在安装...
    "%PYTHON_PATH%" -m pip install -r requirements.txt -q
    echo [OK] 依赖安装完成
)

echo.
echo ================================================
echo           正在启动后端服务...
echo ================================================
echo.
echo 后端地址: http://localhost:8002
echo API文档:  http://localhost:8002/docs
echo.
echo 按 Ctrl+C 停止服务
echo ================================================

:: 启动后端
"%PYTHON_PATH%" -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

pause
