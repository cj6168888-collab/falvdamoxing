# -*- coding: utf-8 -*-
# Check for any remaining corrupted method calls

with open('app/api/adversarial.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all lines that call get_ methods
print("Scanning for method calls...")
for i, line in enumerate(lines):
    if 'get_对手' in line or 'get_我方' in line or 'get_对方' in line:
        # Check if it's corrupted (has replacement character)
        if '\ufffd' in line or '?' in repr(line):
            print(f"Line {i+1}: CORRUPTED - {repr(line)}")
        elif 'get_' in line and 'def ' not in line:
            # This is a method call
            # Verify the method name is correct
            pass  # Already checked above
