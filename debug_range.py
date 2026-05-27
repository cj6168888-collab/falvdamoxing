# -*- coding: utf-8 -*-
with open('app/api/adversarial.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
with open('debug_lines.txt', 'w', encoding='utf-8') as f:
    for i in range(270, 285):
        f.write(f'{i+1}: {repr(lines[i])}\n')
print("Done")
