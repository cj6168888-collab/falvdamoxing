import os
import sqlite3

os.chdir('d:/www/法律大模型')

# 直接使用 SQLite 连接
conn = sqlite3.connect('legal_system.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("SELECT id, title, plaintiff, defendant FROM cases")
rows = cursor.fetchall()

print("Direct SQLite connection results:")
for row in rows:
    print(f"ID: {row['id']}, Title: {row['title']}, Plaintiff: {row['plaintiff']}, Defendant: {row['defendant']}")

# 尝试使用 text_factory 处理字节
print("\n" + "="*60)
print("Testing with different text_factory...")

conn2 = sqlite3.connect('legal_system.db')
conn2.text_factory = lambda b: b.decode('utf-8', errors='replace')

cursor2 = conn2.cursor()
cursor2.execute("SELECT title FROM cases LIMIT 1")
row = cursor2.fetchone()
print(f"Title: {row[0]}")

conn.close()
conn2.close()