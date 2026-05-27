# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

file_path = r"D:\www\法律大模型\app\services\legal_prompts.py"

with open(file_path, 'rb') as f:
    raw = f.read()

original_len = len(raw)

# Characters that Python's tokenizer may reject in identifiers/keywords
# Even inside strings, some Unicode is problematic
# Mapping: problematic_char -> replacement
replacements = [
    # Fullwidth punctuation that might cause issues
    (b'\xe3\x80\x82', b'.'),       # U+3002 ideographic period -> ASCII period
    (b'\xef\xbc\x8c', b','),       # U+FF0C fullwidth comma -> ASCII comma
    (b'\xef\xbc\x9a', b':'),       # U+FF1A fullwidth colon -> ASCII colon
    (b'\xef\xbc\x88', b'('),       # U+FF08 fullwidth left paren -> ASCII
    (b'\xef\xbc\x89', b')'),       # U+FF09 fullwidth right paren -> ASCII
    (b'\xe3\x80\x81', b'~'),       # U+3001 ideographic comma -> ASCII tilde
    # U+2018 U+2019 single quotes
    (b'\xe2\x80\x98', b"'"),
    (b'\xe2\x80\x99', b"'"),
    # U+201C U+201D double quotes
    (b'\xe2\x80\x9c', b'"'),
    (b'\xe2\x80\x9d', b'"'),
    # U+300A U+300B 《》
    (b'\xe3\x80\x8a', b'<'),
    (b'\xe3\x80\x8b', b'>'),
    # U+3008 U+3009 <>
    (b'\xe3\x80\x88', b'<'),
    (b'\xe3\x80\x89', b'>'),
    # U+FF01 fullwidth exclamation -> ASCII !
    (b'\xef\xbc\x81', b'!'),
    # U+FF1F fullwidth question mark -> ASCII ?
    (b'\xef\xbc\x9f', b'?'),
    # U+FF03 # -> ASCII #
    (b'\xef\xbc\x83', b'#'),
    # U+FF0F / -> ASCII /
    (b'\xef\xbc\x8f', b'/'),
    # U+300C U+300D corner brackets
    (b'\xe3\x80\x8c', b'"'),
    (b'\xe3\x80\x8d', b'"'),
    # U+3010 U+3011 brackets
    (b'\xe3\x80\x90', b'['),
    (b'\xe3\x80\x91', b']'),
    # U+300A U+300B
    (b'\xe3\x80\x8a', b'<'),
    (b'\xe3\x80\x8b', b'>'),
]

fixed = raw
total_replacements = 0
for old, new in replacements:
    count = fixed.count(old)
    if count > 0:
        print(f"Replacing {count}x {old.hex()} -> {new.hex()}")
        fixed = fixed.replace(old, new)
        total_replacements += count

print(f"\nTotal replacements: {total_replacements}")
print(f"File size: {original_len} -> {len(fixed)}")

# Write back
with open(file_path, 'wb') as f:
    f.write(fixed)

# Verify with AST
try:
    import ast
    with open(file_path, 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print("AST parse OK!")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}")
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if e.lineno:
        for ln in range(max(0, e.lineno-2), min(len(lines), e.lineno+2)):
            marker = ">>>" if ln+1 == e.lineno else "   "
            print(f"{marker} {ln+1}: {repr(lines[ln][:80])}")
