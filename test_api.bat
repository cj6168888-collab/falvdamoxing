@echo off
chcp 65001 >nul
cd /d d:\www\法律大模型
"C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe" -c "import requests; r = requests.get('http://localhost:8002/health', timeout=5); print('Status:', r.status_code); print(r.json())"
