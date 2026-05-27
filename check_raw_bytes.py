import os
import sqlite3

os.chdir('d:/www/法律大模型')

conn = sqlite3.connect('legal_system.db')
cursor = conn.cursor()

cursor.execute("SELECT title FROM cases WHERE id = 1")
row = cursor.fetchone()

# Get raw bytes
raw_bytes = row[0] if row else None
print(f"Raw bytes type: {type(raw_bytes)}")
print(f"Raw bytes: {raw_bytes}")

if raw_bytes:
    if isinstance(raw_bytes, bytes):
        print(f"Decoded as UTF-8: {raw_bytes.decode('utf-8', errors='replace')}")
        print(f"Decoded as GBK: {raw_bytes.decode('gbk', errors='replace')}")
        print(f"Decoded as Latin-1: {raw_bytes.decode('latin-1', errors='replace')}")
        print(f"Hex: {raw_bytes.hex()}")
    else:
        print(f"As string: {raw_bytes}")
        # Check each character
        print("Character codes:", [ord(c) for c in raw_bytes[:5]])

conn.close()