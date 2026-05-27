#!/usr/bin/env python
import subprocess
import sys
import os

os.chdir(r'D:\www\法律大模型\ui')
sys.exit(subprocess.call([
    r'C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe',
    '-m', 'streamlit', 'run', 'app.py',
    '--server.port', '8501',
    '--server.headless', 'true'
]))
