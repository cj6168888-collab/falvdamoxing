@echo off
chcp 65001 >nul
echo ========================================
echo     法律大模型 - 数据库迁移脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 请访问 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

echo [OK] Python 已找到
echo.

echo [2/3] 运行数据库迁移...
python -c "from app.db.migrate import migrate; migrate()"

if errorlevel 1 (
    echo [错误] 迁移失败
    pause
    exit /b 1
)

echo.
echo [3/3] 迁移完成！
echo.
echo 接下来可以启动后端服务：
echo   启动后端.bat
echo.
pause
