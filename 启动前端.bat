@echo off
chcp 65001 >nul
title 法律案件追踪系统 - 前端服务

cd /d "%~dp0"

echo ================================================
echo        法律案件追踪系统 - 前端服务启动器
echo ================================================
echo.

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [OK] Node.js 已找到
echo.

:: 检查端口是否被占用
netstat -ano | findstr ":3000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 3000 已被占用，正在关闭旧进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 >nul
    echo [OK] 旧进程已关闭
    echo.
)

:: 检查依赖
echo [检查] 正在检查依赖...
if not exist "frontend\node_modules" (
    echo [安装] 正在安装前端依赖...
    cd frontend
    call npm install
    cd ..
    echo [OK] 依赖安装完成
)

echo.
echo ================================================
echo           正在启动前端服务...
echo ================================================
echo.
echo 前端地址: http://localhost:3000
echo 按 Ctrl+C 停止服务
echo ================================================

:: 启动前端
cd frontend
call npm run dev

pause
