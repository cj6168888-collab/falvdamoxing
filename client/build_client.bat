@echo off
chcp 65001 >nul
title 法律大模型 - Windows 客户端构建

echo ========================================
echo   法律大模型 Windows 客户端构建
echo ========================================
echo.

set ROOT=%~dp0..
set CLIENT=%~dp0
set DIST=%CLIENT%dist-exe
set PYTHON_EMBED=%CLIENT%python-embed

:: ==========================================
:: 1. 构建前端
:: ==========================================
echo [1/5] 构建前端...
cd /d "%ROOT%\frontend"
call npm run build 2>&1
if %ERRORLEVEL% neq 0 (
    echo 前端构建失败！
    exit /b 1
)
echo   前端构建完成

:: ==========================================
:: 2. 复制文件到客户端目录
:: ==========================================
echo [2/5] 复制文件...

:: 前端
if exist "%CLIENT%dist" rmdir /s /q "%CLIENT%dist"
xcopy /e /i /q "%ROOT%\frontend\dist" "%CLIENT%dist"

:: 应用代码
if exist "%CLIENT%app" rmdir /s /q "%CLIENT%app"
xcopy /e /i /q "%ROOT%\app" "%CLIENT%app"

:: 环境模板
copy /y "%ROOT%\.env.example" "%CLIENT%\.env"

:: 创建数据目录
if not exist "%CLIENT%data" mkdir "%CLIENT%data"
if not exist "%CLIENT%data\files" mkdir "%CLIENT%data\files"

echo   文件复制完成

:: ==========================================
:: 3. 准备 Python 嵌入式环境
:: ==========================================
echo [3/5] 准备 Python 环境...

:: 检查是否已有嵌入版 Python
if not exist "%PYTHON_EMBED%\python.exe" (
    echo   下载 Python 3.11 嵌入版...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%TEMP%\python-embed.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\python-embed.zip' -DestinationPath '%PYTHON_EMBED%' -Force"
    del "%TEMP%\python-embed.zip"

    :: 启用 pip
    echo import site >> "%PYTHON_EMBED%\python311._pth"

    :: 安装 pip
    echo   安装 pip...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py'"
    "%PYTHON_EMBED%\python.exe" "%TEMP%\get-pip.py" --no-warn-script-location
    del "%TEMP%\get-pip.py"
)

:: 安装客户端依赖
echo   安装依赖...
"%PYTHON_EMBED%\python.exe" -m pip install -r "%CLIENT%\requirements-client.txt" --quiet --no-warn-script-location

echo   Python 环境就绪

:: ==========================================
:: 4. 构建 EXE
:: ==========================================
echo [4/5] 构建 EXE...
"%PYTHON_EMBED%\python.exe" -m pip install pyinstaller --quiet

:: 清理旧构建
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%CLIENT%build" rmdir /s /q "%CLIENT%build"

:: PyInstaller 打包
"%PYTHON_EMBED%\python.exe" -m PyInstaller ^
    --onedir ^
    --name "法律大模型" ^
    --icon "%CLIENT%legal-ai.ico" ^
    --add-data "%CLIENT%dist;client\dist" ^
    --add-data "%CLIENT%app_client.py;client" ^
    --add-data "%ROOT%\app;app" ^
    --hidden-import uvicorn ^
    --hidden-import fastapi ^
    --hidden-import sqlalchemy ^
    --hidden-import pydantic ^
    --noconsole ^
    "%CLIENT%\run_client.py"

if %ERRORLEVEL% neq 0 (
    echo PyInstaller 构建失败！
    exit /b 1
)

:: 移动到 dist-exe
move "%CLIENT%dist\法律大模型" "%DIST%" 2>nul

echo   EXE 构建完成

:: ==========================================
:: 5. 创建安装包
:: ==========================================
echo [5/5] 创建安装包...

:: 检查 Inno Setup
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if "%ISCC%"=="" (
    echo.
    echo [警告] 未找到 Inno Setup 6，跳过安装包创建
    echo 下载地址: https://jrsoftware.org/isinfo.php
    echo.
    echo EXE 文件位置: %DIST%\法律大模型.exe
    goto :done
)

"%ISCC%" "%CLIENT%setup.iss"
echo   安装包创建完成

:done
echo.
echo ========================================
echo   构建完成！
echo   EXE: %DIST%\法律大模型.exe
echo ========================================
pause
