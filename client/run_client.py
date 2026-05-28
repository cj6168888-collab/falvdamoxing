"""
法律大模型 — Windows 桌面客户端

连接到服务器 (fl.jilinpc.com)，在原生窗口中运行。
大模型和服务端逻辑全部在服务器上执行。
"""
import sys
import os

# 默认服务器地址，可通过命令行参数覆盖
SERVER_URL = "https://fl.jilinpc.com"

if len(sys.argv) > 1:
    SERVER_URL = sys.argv[1]


def main():
    try:
        import webview
        window = webview.create_window(
            title="法律大模型 — AI案件指挥台",
            url=SERVER_URL,
            width=1280,
            height=820,
            min_size=(1024, 680),
            resizable=True,
            confirm_close=True,
            text_select=True,
        )
        webview.start(debug=False, http_server=False)
    except ImportError:
        import webbrowser
        import time
        print(f"[法律大模型] 连接到 {SERVER_URL}")
        webbrowser.open(SERVER_URL)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
