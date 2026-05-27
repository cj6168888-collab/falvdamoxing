with open(r'd:\www\法律大模型\app\api\adversarial.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i in range(973, 990):
        line = lines[i]
        print(f'{i+1}: {repr(line)}')
