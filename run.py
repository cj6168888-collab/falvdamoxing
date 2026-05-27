# -*- coding: utf-8 -*-
"""
法律大模型辅助系统 - Windows 启动脚本
"""
import os
import sys
import subprocess
import time
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def clear_screen():
    os.system('cls')

def print_banner():
    print("=" * 60)
    print("⚖️  法律大模型辅助系统")
    print("=" * 60)
    print()

def check_env():
    """检查环境配置"""
    print("📋 检查环境配置...")

    # 检查 .env 文件
    if not os.path.exists('.env'):
        print("⚠️  未找到 .env 文件，正在创建...")
        with open('.env.example', 'r', encoding='utf-8') as f:
            content = f.read()
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 已创建 .env 文件")
        print("   请编辑 .env 文件，填入您的通义千问 API Key")
        print()
        return False

    # 检查 API Key
    with open('.env', 'r', encoding='utf-8') as f:
        env_content = f.read()

    if 'your_api_key_here' in env_content:
        print("⚠️  请先在 .env 文件中配置通义千问 API Key")
        print("   获取地址: https://bailian.console.aliyun.com/")
        print()
        return False

    print("✅ 环境配置完成")
    print()
    return True

def check_dependencies():
    """检查依赖是否安装"""
    print("📦 检查依赖...")

    try:
        import fastapi
        import streamlit
        import sqlalchemy
        import dashscope
        print("✅ 依赖已安装")
        return True
    except ImportError as e:
        print(f"⚠️  缺少依赖: {e}")
        print("   请运行: pip install -r requirements.txt")
        return False

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    print("   访问地址: http://localhost:8002")
    print("   API 文档: http://localhost:8002/docs")
    print()

    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8002"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    return backend_process

def start_frontend():
    """启动前端服务"""
    print("🌐 启动前端服务...")
    print("   访问地址: http://localhost:8501")
    print()

    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ui/app.py", "--server.port", "8501"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    return frontend_process

def main():
    clear_screen()
    print_banner()

    # 检查环境
    if not check_env():
        input("\n按回车键退出...")
        sys.exit(0)

    # 检查依赖
    if not check_dependencies():
        input("\n按回车键退出...")
        sys.exit(0)

    print("=" * 60)
    print("📌 启动说明")
    print("=" * 60)
    print("1. 系统启动后，请访问 http://localhost:8501")
    print("2. 首次使用需要先在左侧创建案件")
    print("3. 上传案件相关材料后，可进行 AI 分析和问答")
    print("=" * 60)
    print()

    try:
        # 启动后端
        backend = start_backend()
        time.sleep(3)

        # 启动前端
        frontend = start_frontend()

        print("✅ 服务已启动！")
        print()
        print("按 Ctrl+C 停止服务")
        print()

        # 等待用户中断
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        backend.terminate()
        frontend.terminate()
        print("✅ 服务已停止")
        sys.exit(0)

if __name__ == "__main__":
    main()
