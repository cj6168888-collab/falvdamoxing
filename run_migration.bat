@echo off
chcp 65001 >nul
cd /d "%~dp0"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe -c "from app.db.migrate import migrate; migrate()"
pause
