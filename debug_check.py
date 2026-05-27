# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

file_path = r"D:\www\法律大模型\app\services\legal_prompts.py"

with open(file_path, 'rb') as f:
    raw = f.read()

lines = raw.split(b'\n')

# Print raw hex for lines 594-597
print("=== Raw bytes 594-597 ===")
for i in range(593, 598):
    line = lines[i]
    print(f"{i+1}: hex={line.hex()}")
    print(f"    ascii-ish: {line.decode('ascii', errors='replace')}")

# Check if there's a """ at the end of line 595
line595 = lines[594]
print(f"\nLine 595: {line595}")
print(f"Line 595 ends with: {line595[-10:].hex()}")

# Search for the function that starts around 510
print("\n=== Lines 505-515 ===")
for i in range(504, 515):
    line = lines[i]
    print(f"{i+1}: {line.decode('utf-8', errors='replace').rstrip(chr(13))}")
