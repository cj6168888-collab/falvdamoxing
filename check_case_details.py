import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("检查案件详情中是否包含 '博凯' 或 '升华'...")

cursor.execute("""
    SELECT id, title, plaintiff, defendant, description, background
    FROM cases
""")
rows = cursor.fetchall()
for r in rows:
    found = False
    for field in ['title', 'plaintiff', 'defendant', 'description', 'background']:
        if r[field] and ('博凯' in r[field] or '升华' in r[field]):
            found = True
            break
    if found:
        print(f"\n找到匹配! ID: {r['id']}")
        print(f"  Title: {r['title']}")
        print(f"  Plaintiff: {r['plaintiff']}")
        print(f"  Defendant: {r['defendant']}")
        print(f"  Description: {str(r['description'])[:200] if r['description'] else 'N/A'}...")

print("\n" + "=" * 60)
print("所有案件完整信息:")
for r in rows:
    print(f"\nID: {r['id']}")
    print(f"  Title: {r['title']}")
    print(f"  Plaintiff: {r['plaintiff']}")
    print(f"  Defendant: {r['defendant']}")
    if r['description']:
        print(f"  Description: {r['description'][:100]}...")

conn.close()