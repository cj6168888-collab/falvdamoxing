import subprocess
import sys
import os

os.chdir(r'D:\www\法律大模型')

# Start the server in background without waiting
if sys.platform == 'win32':
    DETACHED_PROCESS = 0x00000008
    subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=DETACHED_PROCESS
    )
    print("Backend started on port 8000")
else:
    subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    print("Backend started on port 8000")
