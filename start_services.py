# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Start backend
print("Starting backend on port 8002...")
backend = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"],
    cwd=r"D:\www\法律大模型",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=False
)

time.sleep(5)

# Check if backend started
if backend.poll() is None:
    print("Backend started successfully (PID: %d)" % backend.pid)
else:
    output = backend.stdout.read()
    print("Backend failed to start:")
    print(output.decode('utf-8', errors='replace'))
    sys.exit(1)

# Start frontend
print("\nStarting frontend on port 8501...")
frontend = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
    cwd=r"D:\www\法律大模型\ui",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=False
)

time.sleep(5)

if frontend.poll() is None:
    print("Frontend started successfully (PID: %d)" % frontend.pid)
else:
    output = frontend.stdout.read()
    print("Frontend failed to start:")
    print(output.decode('utf-8', errors='replace'))
    sys.exit(1)

print("\n=== Services started ===")
print("Backend:  http://localhost:8002")
print("Backend API docs: http://localhost:8002/docs")
print("Frontend: http://localhost:8501")

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    backend.terminate()
    frontend.terminate()
