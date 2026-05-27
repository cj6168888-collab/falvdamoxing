import subprocess
import sys
import os

os.chdir(r'D:\www\法律大模型')

# Start uvicorn in background
proc = subprocess.Popen([
    sys.executable, '-m', 'uvicorn', 
    'app.main:app', 
    '--host', '0.0.0.0',
    '--port', '8000'
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print(f"Started backend with PID: {proc.pid}")
input("Press Enter to exit and stop the server...")
proc.terminate()