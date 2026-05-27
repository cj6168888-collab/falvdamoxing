import os
import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir('d:/www/法律大模型')

conn = sqlite3.connect('legal_system.db')
cursor = conn.cursor()

print("=" * 60)
print("数据库中的案件数据:")
cursor.execute("SELECT id, title, plaintiff, defendant FROM cases")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}")
    print(f"  标题: {row[1]}")
    print(f"  原告: {row[2]}")
    print(f"  被告: {row[3]}")
    print()

print("=" * 60)
print("证据统计 (案件1):")
cursor.execute("SELECT COUNT(*) FROM evidence_items_v2 WHERE case_id = 1")
count = cursor.fetchone()[0]
print(f"证据数量: {count}")

print("\n" + "=" * 60)
print("证据文件名样例 (前10个):")
cursor.execute("SELECT original_filename FROM evidence_items_v2 WHERE case_id = 1 LIMIT 10")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close()