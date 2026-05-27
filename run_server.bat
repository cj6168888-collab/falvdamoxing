# @echo off
cd /d "%~dp0"
set PYTHONPATH=%cd%
"C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
