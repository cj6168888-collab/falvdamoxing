@echo off
chcp 65001 >nul
cd /d "d:\www\法律大模型"
"C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe" -m streamlit run "ui\app.py" --server.port 8501 --server.headless true
