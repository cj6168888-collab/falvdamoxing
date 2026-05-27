import subprocess
import os
import sys

# Change to project directory
os.chdir(r'D:\www\法律大模型')

# Start uvicorn
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8002'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
)

print(f"Backend started with PID: {proc.pid}")
print("Server running at http://localhost:8000")
print("Press Ctrl+C to stop...")

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
    print("\nServer stopped.")
