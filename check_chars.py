# -*- coding: utf-8 -*-
with open('app/api/adversarial.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The file has corrupted Chinese characters around lines 276-277
# We need to find and fix the broken method definitions
# Looking for patterns like:
# "def get_我方证据(self) -> Optional[str]:\n        return self.X or self.our_evidence"
# where X should be 我方证据, not corrupted text

import re

# Pattern to match the broken get_我方证据 method
# It has corrupted characters in the return statement
old_pattern = r'def get_我方证据\(self\) -> Optional\[str\]:\s*\n\s*return self\.[^\']+ or self\.our_evidence'

# Replace with correct implementation
new_code = '''def get_我方证据(self) -> Optional[str]:
        return self.�Ŝƈ敶 or self.our_evidence'''

# Actually let me try a different approach - find the exact corrupted bytes
# We need to look at the raw bytes to understand the corruption
# Let me just replace the specific range

# First, let's see what's there
with open('app/api/adversarial.py', 'rb') as f:
    raw = f.read()

# Find the position of the broken lines
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'get_我方证据' in line:
        print(f"Line {i+1}: {repr(line)}")
    if 'get_对方证据' in line:
        print(f"Line {i+1}: {repr(line)}")
    if 'return self.' in line and 'or self.our_evidence' in line:
        print(f"Line {i+1}: {repr(line)}")
    if 'return self.' in line and 'or self.opponent_evidence' in line:
        print(f"Line {i+1}: {repr(line)}")
