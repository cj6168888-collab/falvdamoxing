import uvicorn
import logging
from app.main import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('d:/www/法律大模型/api_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    print("Starting API server on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")