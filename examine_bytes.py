# -*- coding: utf-8 -*-
# Examine the actual bytes in the corrupted lines

with open('app/api/adversarial.py', 'rb') as f:
    raw = f.read()

lines = raw.decode('utf-8', errors='replace').split('\n')

out = []
out.append("Examining lines 270-282:")
for i in range(270, 282):
    line = lines[i]
    out.append(f"\nLine {i+1}: {line}")
    # Show hex for non-ASCII
    hex_str = line.encode('utf-8', errors='replace').hex()
    out.append(f"  Hex: {hex_str}")

with open('bytes_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print("Written to bytes_output.txt")
