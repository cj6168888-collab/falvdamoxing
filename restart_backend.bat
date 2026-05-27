@echo off
chcp 65001 >nul
cd /d "d:\www\法律大模型"
echo Restarting backend...
taskkill /F /IM python.exe 2>nul
timeout /t 2 >nul
echo Starting backend...
start /b "" cmd /c "C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo Backend restart initiated.
