import os
print(f"Current working directory: {os.getcwd()}")
print(f"Database path in config: sqlite:///./legal_system.db")
print(f"Absolute path would be: {os.path.abspath('legal_system.db')}")

# 检查这些文件是否存在
paths = [
    'legal_system.db',
    './legal_system.db',
    'd:/www/法律大模型/legal_system.db',
    './data/law_assistant.db'
]
for p in paths:
    exists = os.path.exists(p)
    size = os.path.getsize(p) if exists else 0
    print(f"{p}: {'EXISTS' if exists else 'NOT FOUND'} ({size} bytes)")