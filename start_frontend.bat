@echo off
chcp 65001 >nul
cd /d "d:\www\法律大模型"
echo Starting Streamlit with correct path handling...
"C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe" -c "
import subprocess
import sys
import os
os.chdir(r'd:\www\法律大模型\ui')
sys.exit(subprocess.call([sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.port', '8501', '--server.headless', 'true']))
"
