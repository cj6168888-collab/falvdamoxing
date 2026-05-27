import sys
import subprocess
import time
import os

os.chdir(r'D:\www\法律大模型')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

python_path = r'C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe'

proc = subprocess.Popen(
    [python_path, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8002'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace'
)

time.sleep(8)

import urllib.request
try:
    resp = urllib.request.urlopen('http://localhost:8002/health', timeout=5)
    print('Status:', resp.status)
    print('Body:', resp.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)

proc.kill()
output, _ = proc.communicate(timeout=5)
print('\n--- Server Output ---')
print(output)
