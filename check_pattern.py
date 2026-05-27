with open(r'd:\www\法律大模型\app\api\adversarial.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check what we have
print("Checking for old async text:")
old_seq1 = "our_evidence=data.对方证据 or \"\""
old_seq2 = "our_evidence=data.对方证据"
if old_seq1 in content:
    print(f"FOUND: {repr(old_seq1)}")
else:
    print(f"NOT FOUND: {repr(old_seq1)}")
    
# Find all occurrences
import re
matches = list(re.finditer(r'our_evidence=data\.[^)]+', content))
for m in matches:
    print(f"Match at {m.start()}: {repr(m.group())}")
