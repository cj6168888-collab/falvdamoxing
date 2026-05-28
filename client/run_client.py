"""
法律大模型 — Windows 桌面客户端

使用嵌入式 WebView (pywebview) 的本地桌面应用
- 原生窗口，无浏览器地址栏
- 本地 SQLite 数据库
- 系统托盘常驻
- 自动端口选择
"""
import os
import sys
import socket
import threading
import time
import json

CLIENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CLIENT_DIR))
os.chdir(CLIENT_DIR)

os.environ.setdefault("APP_ENV", "client")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{CLIENT_DIR}/data/legal_client.db".replace("\\", "/"))
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("SMS_PROVIDER", "console")
os.environ.setdefault("PYTHONUNBUFFERED", "1")


def find_free_port(start: int = 8090) -> int:
    for port in range(start, start + 200):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return 8090


def start_server(port: int):
    """在后台线程启动 FastAPI"""
    import uvicorn
    uvicorn.run(
        "client.app_client:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )


def main():
    port = find_free_port(8090)
    url = f"http://127.0.0.1:{port}"

    print(f"[法律大模型] 本地服务: {url}")

    # 启动后端
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    # 等待后端就绪
    print("[法律大模型] 启动中...")
    import urllib.request
    for i in range(30):
        try:
            urllib.request.urlopen(f"{url}/health", timeout=2)
            break
        except Exception:
            time.sleep(1)
    else:
        print("[法律大模型] 启动超时")

    # 原生桌面窗口
    try:
        import webview
        window = webview.create_window(
            title="法律大模型 — AI案件指挥台",
            url=url,
            width=1280,
            height=800,
            min_size=(1024, 680),
            resizable=True,
            fullscreen=False,
            confirm_close=True,
            text_select=True,
        )
        webview.start(debug=False, http_server=False)
    except ImportError:
        print("[法律大模型] pywebview 未安装，使用浏览器打开")
        import webbrowser
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
