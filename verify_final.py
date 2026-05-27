# -*- coding: utf-8 -*-
# Final verification of all getter methods

with open('app/api/adversarial.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Verifying getter methods:")
for i, line in enumerate(lines):
    if 'def get_' in line and 'self)' in line and 'Optional' in line:
        next_line = lines[i+1] if i+1 < len(lines) else ''
        print(f"\nLine {i+1}: {line.strip()}")
        print(f"Line {i+2}: {next_line.strip()}")
        
        # Verify correctness
        errors = []
        if 'get_对手名称' in line:
            if 'self.\u5bf9\u624b\u540d\u79f0 or self.opponent_name' not in next_line:
                errors.append("Wrong return value")
        elif 'get_对手类型' in line:
            if 'self.\u5bf9\u624b\u7c7b\u578b or self.opponent_type' not in next_line:
                errors.append("Wrong return value")
        elif 'get_我方证据' in line:
            if 'self.\u5bf9\u65b9\u8bc1\u636e or self.our_evidence' not in next_line:
                errors.append("Wrong return value")
        elif 'get_对方证据' in line:
            if 'self.\u5bf9\u65b9\u8bc1\u636e or self.opponent_evidence' not in next_line:
                errors.append("Wrong return value")
        
        if errors:
            print(f"  ERRORS: {errors}")
        else:
            print(f"  OK")
