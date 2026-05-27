#!/bin/bash
# 法律大模型辅助系统 - Linux/Mac 启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}⚖️  法律大模型辅助系统${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# 检查环境配置
echo -e "${YELLOW}📋 检查环境配置...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件，正在创建...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ 已创建 .env 文件${NC}"
    echo -e "${YELLOW}   请编辑 .env 文件，填入您的通义千问 API Key${NC}"
    echo ""
    exit 1
fi

# 检查 API Key
if grep -q "your_api_key_here" .env; then
    echo -e "${YELLOW}⚠️  请先在 .env 文件中配置通义千问 API Key${NC}"
    echo -e "${YELLOW}   获取地址: https://bailian.console.aliyun.com/${NC}"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ 环境配置完成${NC}"
echo ""

# 检查依赖
echo -e "${YELLOW}📦 检查依赖...${NC}"
python3 -c "import fastapi, streamlit, sqlalchemy, dashscope" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  缺少依赖，请运行: pip install -r requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 依赖已安装${NC}"
echo ""

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}📌 启动说明${NC}"
echo -e "${GREEN}============================================================${NC}"
echo "1. 系统启动后，请访问 http://localhost:8501"
echo "2. 首次使用需要先在左侧创建案件"
echo "3. 上传案件相关材料后，可进行 AI 分析和问答"
echo -e "${GREEN}============================================================${NC}"
echo ""

# 启动后端
echo -e "${YELLOW}🚀 启动后端服务...${NC}"
echo -e "${YELLOW}   访问地址: http://localhost:8000${NC}"
echo -e "${YELLOW}   API 文档: http://localhost:8000/docs${NC}"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

# 启动前端
echo ""
echo -e "${YELLOW}🌐 启动前端服务...${NC}"
echo -e "${YELLOW}   访问地址: http://localhost:8501${NC}"
echo ""

streamlit run ui/app.py --server.port 8501 &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✅ 服务已启动！${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo ""

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo -e '${GREEN}✅ 服务已停止${NC}'; exit 0" SIGINT SIGTERM

wait
