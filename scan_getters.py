# -*- coding: utf-8 -*-
# Fix all corrupted getter method names and return statements in adversarial.py

with open('app/api/adversarial.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Scanning for all getter methods...")

# Scan all getter methods
for i, line in enumerate(lines):
    if 'def get_' in line and 'self)' in line and 'Optional' in line:
        next_line = lines[i+1] if i+1 < len(lines) else ''
        print(f"Line {i+1}: {repr(line)}")
        print(f"Line {i+2}: {repr(next_line)}")
        print("---")
