import sys
import subprocess
import time
import os

os.chdir(r'D:\www\法律大模型\frontend')
sys.stdout.reconfigure(encoding='utf-8')

proc = subprocess.Popen(
    ['npx.cmd', 'vite', '--port', '3000'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace'
)

time.sleep(8)

import urllib.request
try:
    resp = urllib.request.urlopen('http://localhost:3000', timeout=5)
    print('Status:', resp.status)
except Exception as e:
    print('Error:', e)

proc.kill()
output, _ = proc.communicate(timeout=5)
print('\n--- Frontend Output ---')
lines = output.strip().split('\n')
for line in lines[-10:]:
    print(line)
