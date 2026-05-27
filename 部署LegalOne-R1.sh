#!/bin/bash
# ==========================================
#   LegalOne-R1 模型部署脚本 (Linux/macOS)
#   法律大模型 SaaS 升级 - 第4阶段
# ==========================================

set -e

# 配置
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
MODELS_DIR="${HOME}/.ollama/models"

echo "=========================================="
echo "  LegalOne-R1 模型部署脚本"
echo "=========================================="
echo ""

# 检查 Ollama
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        echo "[错误] Ollama 未安装"
        echo "请访问 https://ollama.com/download 安装"
        exit 1
    fi
    echo "[OK] Ollama 已安装 ($(ollama --version))"
}

# 检查服务状态
check_service() {
    if curl -s "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
        echo "[OK] Ollama 服务正在运行 (${OLLAMA_URL})"
        return 0
    else
        echo "[警告] Ollama 服务未运行"
        echo "请执行: ollama serve"
        return 1
    fi
}

# 列出已安装模型
list_models() {
    echo ""
    echo "已安装模型:"
    ollama list
    echo ""
}

# 安装 LegalOne-R1 8B
install_8b() {
    echo ""
    echo "[1/2] 拉取 LegalOne-R1 8B (~5-8GB)"
    echo "      模型: THUIR/LegalOne-R1 (Qwen3-8B)"
    echo "      用途: 法律推理、文书生成、法律咨询"
    echo ""
    ollama pull legalone-r1:8b
    echo "[成功] LegalOne-R1 8B 安装完成"
}

# 安装 LegalOne-R1 4B
install_4b() {
    echo ""
    echo "[1/2] 拉取 LegalOne-R1 4B (~2.5GB)"
    echo "      模型: THUIR/LegalOne-R1 (Qwen3-4B)"
    echo "      用途: 法律推理 (RTX 3060 可用)"
    echo ""
    ollama pull legalone-r1:4b
    echo "[成功] LegalOne-R1 4B 安装完成"
}

# 检查磁盘空间
check_disk() {
    local required=$1
    local available=$(df -h "$HOME" | awk 'NR==2 {print $4}')
    echo "磁盘可用空间: ${available}"
}

# 主菜单
show_menu() {
    echo "【模型列表】"
    echo "  1. legalone-r1:8b  - LegalOne-R1 8B (推荐 RTX 4090/A100)"
    echo "  2. legalone-r1:4b  - LegalOne-R1 4B (RTX 3060 12GB 可用)"
    echo "  3. qwen2.5:14b     - Qwen2.5 14B (通用推理)"
    echo "  4. 全部安装"
    echo "  5. 仅检查状态"
    echo ""
    read -p "请选择 (1-5): " choice
    case $choice in
        1) check_ollama && check_service && install_8b && list_models ;;
        2) check_ollama && check_service && install_4b && list_models ;;
        3) check_ollama && check_service && ollama pull qwen2.5:14b && list_models ;;
        4) check_ollama && check_service && install_4b && ollama pull qwen2.5:14b && list_models ;;
        5) check_ollama && check_service && list_models ;;
        *) echo "无效选择" ;;
    esac
}

# 命令行参数支持
if [ $# -gt 0 ]; then
    check_ollama
    case $1 in
        install-8b) check_service && install_8b && list_models ;;
        install-4b) check_service && install_4b && list_models ;;
        status) check_service && list_models ;;
        *) echo "用法: $0 [install-8b|install-4b|status]" ;;
    esac
else
    show_menu
fi

echo ""
echo "=========================================="
echo "参考文档:"
echo "  LegalOne-R1: https://github.com/THUIR/LegalOne-R1"
echo "  DISC-LawLLM: https://github.com/FudanDISC/DISC-LawLLM"
echo "=========================================="
