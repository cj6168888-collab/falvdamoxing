@echo off
chcp 65001 >nul
cd /d d:\www\法律大模型
echo Starting backend on port 8002...
C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
pause
