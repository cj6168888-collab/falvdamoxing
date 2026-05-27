import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("检查 cases 表中的中文数据...")

cursor.execute("SELECT id, title, plaintiff, defendant FROM cases")
rows = cursor.fetchall()

for r in rows:
    title = r['title']
    plaintiff = r['plaintiff']
    defendant = r['defendant']
    print(f"ID: {r['id']}")
    print(f"  Title: {title}")
    print(f"  Plaintiff: {plaintiff}")
    print(f"  Defendant: {defendant}")
    print()

# 直接查看数据库文件的二进制内容
print("=" * 60)
print("检查数据库编码...")

# 检查 PRAGMA encoding
cursor.execute("PRAGMA encoding")
encoding = cursor.fetchone()
print(f"Database encoding: {encoding[0]}")

conn.close()