@echo off
chcp 65001 >nul
title 法律大模型 - Ollama服务管理

:: 检查是否以管理员权限运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 建议以管理员权限运行此脚本以获得最佳体验
)

echo ============================================
echo       法律大模型 - Ollama 服务管理
echo ============================================
echo.

:: 检查Ollama是否已安装
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [1] Ollama 未安装，正在下载安装...
    powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://ollama.com/install.ps1' -OutFile '$env:TEMP\ollama-install.ps1'; Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File $env:TEMP\ollama-install.ps1'"
    echo 安装程序已启动，请在弹出的窗口中完成安装
    pause
    exit /b
)

:: Ollama已安装，显示状态
echo [检查] Ollama 状态...

:: 检查Ollama服务是否运行
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama 服务正在运行
    echo.
    
    :: 显示可用模型
    echo [信息] 可用模型列表:
    curl -s http://localhost:11434/api/tags | findstr /r "name"
    echo.
    
    :MENU
    echo ============================================
    echo                  操 作 菜 单
    echo ============================================
    echo  [1] 查看已安装模型
    echo  [2] 下载 llama2 模型 (约3.8GB)
    echo  [3] 下载 gemma4:e4b 模型 (约9.6GB) [推荐]
    echo  [4] 下载 gemma4:e2b 模型 (约7.2GB)
    echo  [5] 下载 gemma4:26b 模型 (约18GB)
    echo  [6] 下载 gemma4:31b 模型 (约20GB)
    echo  [7] 下载 mistral 模型 (约4.1GB)
    echo  [8] 下载 qwen:2.5 模型 (约2.3GB)
    echo  [9] 自定义下载模型
    echo  [10] 启动/重启 Ollama 服务
    echo  [11] 停止 Ollama 服务
    echo  [12] 测试 Ollama 连接
    echo  [0] 退出
    echo ============================================
    echo.
    set /p choice=请输入选项 [0-9]:
    
    if "%choice%"=="1" goto LIST_MODELS
    if "%choice%"=="2" goto PULL_LLAMA2
    if "%choice%"=="3" goto PULL_GEMMA4_E4B
    if "%choice%"=="4" goto PULL_GEMMA4_E2B
    if "%choice%"=="5" goto PULL_GEMMA4_26B
    if "%choice%"=="6" goto PULL_GEMMA4_31B
    if "%choice%"=="7" goto PULL_MISTRAL
    if "%choice%"=="8" goto PULL_QWEN
    if "%choice%"=="9" goto CUSTOM_PULL
    if "%choice%"=="10" goto RESTART_SERVICE
    if "%choice%"=="11" goto STOP_SERVICE
    if "%choice%"=="12" goto TEST_CONNECTION
    if "%choice%"=="0" goto END
    
    echo 无效选项，请重试
    goto MENU
    
    :LIST_MODELS
    echo.
    echo [信息] 已安装模型列表:
    curl -s http://localhost:11434/api/tags
    echo.
    goto MENU
    
    :PULL_LLAMA2
    echo.
    echo [下载] 开始下载 llama2 模型...
    echo 提示: 下载过程可能需要5-15分钟，取决于网络速度
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull llama2"
    echo [完成] llama2 下载完成
    goto MENU
    
    :PULL_GEMMA2B
    echo.
    echo [下载] 开始下载 gemma4:e2b 模型...
    echo 提示: 下载过程可能需要10-30分钟
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull gemma4:e2b"
    echo [完成] gemma4:e2b 下载完成
    goto MENU
    
    :PULL_GEMMA4_E4B
    echo.
    echo [下载] 开始下载 gemma4:e4b 模型 (推荐)...
    echo 提示: 下载过程可能需要20-60分钟，取决于网络速度
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull gemma4:e4b"
    echo [完成] gemma4:e4b 下载完成
    goto MENU
    
    :PULL_GEMMA4_E2B
    echo.
    echo [下载] 开始下载 gemma4:e2b 模型...
    echo 提示: 下载过程可能需要15-40分钟
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull gemma4:e2b"
    echo [完成] gemma4:e2b 下载完成
    goto MENU
    
    :PULL_GEMMA4_26B
    echo.
    echo [下载] 开始下载 gemma4:26b 模型...
    echo 警告: 此模型较大(约18GB)，需要较大磁盘空间
    echo 提示: 下载过程可能需要30-90分钟
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull gemma4:26b"
    echo [完成] gemma4:26b 下载完成
    goto MENU
    
    :PULL_GEMMA4_31B
    echo.
    echo [下载] 开始下载 gemma4:31b 模型...
    echo 警告: 此模型较大(约20GB)，需要较大磁盘空间
    echo 提示: 下载过程可能需要30-90分钟
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull gemma4:31b"
    echo [完成] gemma4:31b 下载完成
    goto MENU
    
    :PULL_MISTRAL
    echo.
    echo [下载] 开始下载 mistral 模型...
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull mistral"
    echo [完成] mistral 下载完成
    goto MENU
    
    :PULL_QWEN
    echo.
    echo [下载] 开始下载 qwen2.5 模型...
    echo.
    start /wait cmd /c "title Ollama 下载中... && ollama pull qwen2.5:3b"
    echo [完成] qwen2.5 下载完成
    goto MENU
    
    :CUSTOM_PULL
    echo.
    echo [提示] 可用模型示例:
    echo   - gemma4:e4b (推荐)
    echo   - gemma4:e2b
    echo   - gemma4:26b
    echo   - gemma4:31b
    echo   - llama2
    echo   - mistral
    echo   - qwen2.5:3b
    echo.
    set /p model_name=请输入模型名称:
    if "%model_name%"=="" goto CUSTOM_PULL
    echo.
    echo [下载] 开始下载 %model_name%...
    start /wait cmd /c "title Ollama 下载中... && ollama pull %model_name%"
    echo [完成] %model_name% 下载完成
    goto MENU
    
    :RESTART_SERVICE
    echo.
    echo [重启] 正在重启 Ollama 服务...
    taskkill /f /im ollama.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    start /b ollama serve
    timeout /t 3 /nobreak >nul
    echo [完成] Ollama 服务已重启
    goto MENU
    
    :STOP_SERVICE
    echo.
    echo [停止] 正在停止 Ollama 服务...
    taskkill /f /im ollama.exe >nul 2>&1
    echo [完成] Ollama 服务已停止
    goto MENU
    
    :TEST_CONNECTION
    echo.
    echo [测试] 正在测试 Ollama 连接...
    curl -s http://localhost:11434/api/tags
    if %errorlevel% equ 0 (
        echo.
        echo [成功] Ollama 连接正常!
    ) else (
        echo.
        echo [失败] 无法连接到 Ollama 服务
        echo 请确保 Ollama 服务正在运行
    )
    goto MENU
    
) else (
    echo [警告] Ollama 服务未运行
    echo.
    
    :START_MENU
    echo ============================================
    echo              启 动 选 项
    echo ============================================
    echo  [1] 启动 Ollama 服务 (默认端口11434)
    echo  [2] 启动 Ollama 服务 (自定义端口)
    echo  [3] 下载并安装 Ollama
    echo  [0] 退出
    echo ============================================
    echo.
    set /p choice=请输入选项 [0-3]:
    
    if "%choice%"=="1" goto START_DEFAULT
    if "%choice%"=="2" goto START_CUSTOM
    if "%choice%"=="3" goto INSTALL
    if "%choice%"=="0" goto END
    
    echo 无效选项，请重试
    goto START_MENU
    
    :START_DEFAULT
    echo.
    echo [启动] 正在启动 Ollama 服务...
    start /b ollama serve
    timeout /t 3 /nobreak >nul
    
    :: 验证启动
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo [成功] Ollama 服务已启动!
        echo.
        echo [信息] 服务地址: http://localhost:11434
        echo [信息] API文档: http://localhost:11434/docs
        echo.
        
        :: 检查是否有模型
        set models=0
        for /f "delims=" %%i in ('curl -s http://localhost:11434/api/tags ^| findstr /c:"name"') do set /a models+=1
        if %models% equ 0 (
            echo [提示] 未检测到已安装的模型
            echo 建议运行此脚本下载一个模型
        )
        
    ) else (
        echo [失败] Ollama 服务启动失败
        echo 请检查日志或手动启动 ollama serve
    )
    goto END
    
    :START_CUSTOM
    echo.
    set /p port=请输入端口号 (默认11434):
    if "%port%"=="" set port=11434
    echo.
    echo [启动] 正在启动 Ollama 服务，端口: %port%
    set OLLAMA_HOST=0.0.0.0:%port%
    start /b cmd /c "set OLLAMA_HOST=%port% && ollama serve"
    timeout /t 3 /nobreak >nul
    echo [信息] Ollama 已在后台启动
    goto END
    
    :INSTALL
    echo.
    echo [安装] 正在启动 Ollama 安装程序...
    powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File $env:TEMP\ollama-install.ps1'"
    echo 安装程序已启动，请在弹出的窗口中完成安装
    goto END
)

:END
echo.
echo ============================================
echo              脚本执行完毕
echo ============================================
echo.
pause
