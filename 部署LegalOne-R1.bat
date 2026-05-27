@echo off
chcp 65001 >nul
echo ==========================================
echo   LegalOne-R1 模型部署脚本
echo   法律大模型 SaaS 升级 - 第4阶段
echo ==========================================
echo.
echo 【说明】
echo   本脚本用于在本地 Ollama 中部署法律专项大模型
echo   模型将下载到 D:\www\法律大模型\models\ 目录
echo.
echo 【模型列表】
echo   1. legalone-r1:8b  - LegalOne-R1 8B (推荐 RTX 4090/A100)
echo   2. legalone-r1:4b  - LegalOne-R1 4B (RTX 3060 12GB 可用)
echo   3. disc-lawllm:7b  - DISC-LawLLM 7B (Qwen2.5 基座)
echo   4. 全部安装
echo   5. 仅检查状态
echo.
echo 【磁盘空间要求】
echo   legalone-r1:8b  ~ 5-8 GB
echo   legalone-r1:4b  ~ 2.5 GB
echo   disc-lawllm:7b ~ 4 GB
echo.
echo ==========================================
echo.

set /p CHOICE=请选择 (1-5):

if "%CHOICE%"=="1" goto INSTALL_8B
if "%CHOICE%"=="2" goto INSTALL_4B
if "%CHOICE%"=="3" goto INSTALL_DISC
if "%CHOICE%"=="4" goto INSTALL_ALL
if "%CHOICE%"=="5" goto CHECK_STATUS
goto END

:INSTALL_8B
echo.
echo [1/2] 正在安装 ollama (如果尚未安装)...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo 请先安装 Ollama: https://ollama.com/download
    echo 安装后请将 ollama 添加到系统 PATH
    pause
    exit /b 1
)
echo [OK] Ollama 已安装
echo.
echo [2/2] 开始拉取 LegalOne-R1 8B (~5-8GB，预计 10-30 分钟)
echo    模型: THUIR/LegalOne-R1 (Qwen3-8B 基座)
echo    用途: 法律推理、文书生成、法律咨询
echo.
ollama pull legalone-r1:8b
if %errorlevel% equ 0 (
    echo.
    echo [成功] LegalOne-R1 8B 安装完成!
    echo.
    echo 验证安装:
    ollama list
) else (
    echo.
    echo [失败] 模型拉取失败，请检查网络连接和磁盘空间
)
goto END

:INSTALL_4B
echo.
echo [1/2] 检查 Ollama...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo 请先安装 Ollama: https://ollama.com/download
    pause
    exit /b 1
)
echo [OK] Ollama 已安装
echo.
echo [2/2] 开始拉取 LegalOne-R1 4B (~2.5GB，预计 5-15 分钟)
echo    模型: THUIR/LegalOne-R1 (Qwen3-4B 基座)
echo    用途: 法律推理、文书生成 (轻量版)
echo.
ollama pull legalone-r1:4b
if %errorlevel% equ 0 (
    echo.
    echo [成功] LegalOne-R1 4B 安装完成!
    echo.
    echo 验证安装:
    ollama list
) else (
    echo.
    echo [失败] 模型拉取失败
)
goto END

:INSTALL_DISC
echo.
echo [1/2] 检查 Ollama...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo 请先安装 Ollama: https://ollama.com/download
    pause
    exit /b 1
)
echo [OK] Ollama 已安装
echo.
echo [2/2] 开始拉取 DISC-LawLLM 7B (~4GB，预计 8-20 分钟)
echo    模型: FudanDISC/DISC-LawLLM (Qwen2.5-7B 基座)
echo    用途: 法律问答、条文引用、案例分析
echo.
ollama pull qwen2.5:7b
if %errorlevel% equ 0 (
    echo.
    echo [成功] Qwen2.5 7B 基座安装完成
    echo.
    echo 注意: DISC-LawLLM 需要微调权重
    echo 完整安装请参考: https://github.com/FudanDISC/DISC-LawLLM
    echo.
    echo 验证安装:
    ollama list
) else (
    echo.
    echo [失败] 模型拉取失败
)
goto END

:INSTALL_ALL
echo.
echo 开始安装全部法律模型...
echo.
echo [步骤1] 安装 LegalOne-R1 4B (轻量版)
ollama pull legalone-r1:4b
echo.
echo [步骤2] 安装 Qwen2.5 14B (通用推理)
ollama pull qwen2.5:14b
echo.
echo [完成] 全部模型安装完成
echo.
echo 当前已安装模型:
ollama list
goto END

:CHECK_STATUS
echo.
echo 检查 Ollama 状态...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Ollama 未安装
    echo 请访问 https://ollama.com/download 安装
    goto END
)
echo [OK] Ollama 已安装
echo.
echo 已安装模型:
ollama list
echo.
echo Ollama 服务状态:
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama 服务正在运行 (http://localhost:11434)
) else (
    echo [警告] Ollama 服务未运行，请执行: ollama serve
)
echo.
echo 快速测试 (使用 qwen2.5:7b):
echo 输入 exit 退出测试
ollama run qwen2.5:7b "用一句话介绍自己"
goto END

:END
echo.
echo ==========================================
echo 操作完成
echo.
echo 后续步骤:
echo   1. 启动 Ollama: ollama serve
echo   2. 启动法律大模型系统
echo   3. 在系统设置中选择使用的模型
echo.
echo 参考文档:
echo   LegalOne-R1: https://github.com/THUIR/LegalOne-R1
echo   DISC-LawLLM: https://github.com/FudanDISC/DISC-LawLLM
echo ==========================================
pause
