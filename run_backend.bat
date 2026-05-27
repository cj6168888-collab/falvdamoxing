@echo off
chcp 65001 >nul
cd /d d:\www\法律大模型
start /b C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002
timeout /t 5 /nobreak >nul
