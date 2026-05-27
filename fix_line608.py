# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

file_path = r"D:\www\法律大模型\app\services\legal_prompts.py"

with open(file_path, 'rb') as f:
    raw = f.read()

lines = raw.split(b'\n')

# Check lines 609-613
print("=== Lines 609-613 raw ===")
for i in range(608, 614):
    line = lines[i]
    print(f"{i+1}: hex={line.hex()}")
    print(f"    chars: {repr(line.decode('utf-8', errors='replace').rstrip(chr(13)))}")

# So line 609 (0-indexed 608) is a blank line
# Line 610 (0-indexed 609): # 添加案件处理方向
# Line 611 (0-indexed 610): prompt += "\n\n" + get_direction_prompt(case_direction)
# Line 612 (0-indexed 611): return prompt
# 
# The string starting at line 597 (prompt += """)
# should close somewhere before line 610
# But line 610 starts with "prompt" which is code...
# So the string MUST close at line 609

# But line 609 is BLANK with 4 spaces (hex 20202020)
# That's weird. A blank line with 4 spaces inside a string?

# Let me check: does line 609 actually have 4 spaces and then """?
# Hex shows: 202020200d -> that's 4 spaces + CR
# NO triple quotes!

# So where does the string end?
# Line 610 starts with prompt... and line 611 is return...
# Both are code lines at 4-space indentation
# But line 610 is the first line AFTER the string that doesn't have the """
# Wait... maybe line 610 doesn't have """
# But line 609 doesn't have """
# Line 608 is blank...
# 
# AHA! Line 608 is the LAST line of the string content
# And the string doesn't close on line 608
# The string is unclosed!

# But Python didn't report "unclosed string" - it reported "expected indented block at 583"
# Why? Because Python's tokenizer may get confused when there's a lot of content

# Let me check: where should the triple-quote close?
# The string content from line 597 includes lines 598-608
# Then the NEXT statement is at line 610
# So the triple-quote should close at line 609

# But line 609 is just "    " (4 spaces) - no closing """
# So I need to change line 609 to add """
# at the end of the line

# Actually wait. Let me reconsider. The hex of line 609 is 0d (just CR).
# But line 608 is the last line of the string content
# For a triple-quoted string, the closing """ needs to be ON a line
# Let me check if line 608 might have the closing """

# Line 608 hex: 0d -> just CR. No content.
# So the closing """ is MISSING after line 608

# But wait, the actual file content shows line 609 as "    # 添加案件处理方向"
# That's AFTER the string should close

# Let me try another approach: what if the string closes on a later line
# that I'm missing? Let me look at the ORIGINAL debug output again:
# 609: b'    # \xe6\xb7\xbb\xe5\x8a\xa0\xe6\xa1\x88\xe4\xbb\xb6\xe5\xa4\x84\xe7\x90\x86\xe6\x96\xb9\xe5\x90\x91\r'
# That's "# 添加案件处理方向" at 4-space indent
# 610: b'    prompt += "\\n\\n" + get_direction_prompt(case_direction)\r'
# 611: b'    return prompt\r'

# So the structure is:
# Line 597: prompt += """
# Lines 598-608: string content
# Line 609: comment inside else block (at 4 spaces) - BUT THIS IS STRING CONTENT
# Line 610: code (prompt += ...)
# Line 611: code (return prompt)
# 
# For this to be valid Python:
# The string from line 597 must close before line 610
# Line 609 should have the closing """
# But it has "# 添加..." instead

# So line 609 is MISSING the closing """
# I need to add """ at the end of line 609

# But first, let me confirm: what's on line 609 exactly?
print(f"\nLine 609 (index 608): {lines[608]}")
print(f"Line 610 (index 609): {lines[609]}")

# Hmm, the raw file has line 609 as just 4 spaces (hex 202020200d)
# But the Python output earlier showed it as "    # 添加..."
# That's because of how the file was split...

# Wait, let me re-count. lines[] is split by \n.
# With CRLF (\r\n), each line ends with \r and the last one might not have \n.
# The raw file has \r line endings.

# Let me check the actual line content again more carefully.
# The debug output from the "Full context" shows:
# 608: ''
# 609: '    # 添加案件处理方向'
# 610: '    prompt += "\\n\\n" + get_direction_prompt(case_direction)'
# 611: '    return prompt'

# But in the raw hex dump:
# Line 608: 0d (just CR)
# Line 609: 202020202320e6b7bbe58aa0... (4 spaces + # comment)
# Line 610: 2020202070726f6d7074... (4 spaces + prompt +=)
# Line 611: 2020202070726f6d7074... (4 spaces + return prompt)

# So line 608 is blank (4 spaces + CR)
# Line 609 is a comment at 4-space indent
# Line 610 is code at 4-space indent
# Line 611 is code at 4-space indent

# The string starting at line 597 (prompt += """) contains:
# Line 598: blank
# Line 599-604: markdown content
# Line 605: comment inside string (4 spaces + # comment)
# Line 606: code inside string (4 spaces + if case_direction...)
# Line 607: code inside string (8 spaces + prompt +=...)
# Line 608: blank at 4 spaces (string content)
# 
# And then the string must close before line 609
# So line 609 should start with """
# But it's "    # 添加..." instead

# So the bug is: the triple-quote that closes the string
# on line 597 is MISSING

# I need to add """ at the end of line 608 (or at the start of line 609)
# Line 609 currently starts with "    # 添加..."
# The "    " is indentation, and "# 添加..." is a Python comment
# For the string to close, the line should be `"""` or the closing """
# needs to be on the previous line

# Looking at the original raw file:
# Line 608: 0d (just a blank line with implied continuation of string)
# But the string content includes line 608 which is blank
# The closing """ must be on a line
# Currently, line 609 starts with code (at 4 spaces)
# This means the string is UNCLOSED

# Fix: Change line 608 to contain """ at the end
# Currently: 0d -> should be: """ followed by \r

# Wait, but the "Full context" output shows line 608 as '' (empty)
# and the raw hex shows it as 0d
# Let me look again at the raw hex output:
# Line 608: 0d -> just CR, no spaces, no content

# So the fix is:
# Add """ at the end of line 608
# Change hex from: 0d
# To: 2222220d ("\"" + CR)

# Let me do that fix
print("\n=== Fixing the missing closing triple-quote ===")
print("Line 608 (index 607):")
print(f"  Before: {lines[607].hex()}")

# Wait, let me do it properly
lines[607] = b'"""' + b'\r'
print(f"  New: {lines[607].hex()}")

# Now try parsing
content = b'\n'.join(lines).decode('utf-8', errors='replace')
import ast
try:
    ast.parse(content)
    print("Full file now parses OK!")
except SyntaxError as e:
    print(f"Still error at line {e.lineno}: {e.msg}")
    cl = content.split('\n')
    for i in range(max(0, e.lineno-3), min(len(cl), e.lineno+3)):
        marker = ">>>" if i+1 == e.lineno else "   "
        print(f"  {marker} {i+1}: {repr(cl[i][:100])}")

# Write the fixed file
with open(file_path, 'wb') as f:
    f.write(b'\n'.join(lines))

print("\nFixed file written.")
