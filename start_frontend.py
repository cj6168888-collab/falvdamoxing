#!/usr/bin/env python
import subprocess
import sys
import os

os.chdir(r'd:\www\法律大模型\ui')
sys.exit(subprocess.call([sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.port', '8501', '--server.headless', 'true']))
