@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在运行数据库迁移...
C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe -c "from app.db.migrate import migrate; migrate()"
pause