import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 搜索证据文件名包含博凯或升华
print("=" * 60)
print("搜索证据文件名包含 '博凯' 或 '升华'...")
cursor.execute("SELECT id, case_id, original_filename FROM evidence_items_v2 WHERE original_filename LIKE '%博凯%' OR original_filename LIKE '%升华%' LIMIT 20")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条")

# 搜索证据内容包含博凯或升华
print("\n" + "=" * 60)
print("搜索证据内容包含 '博凯' 或 '升华'...")
cursor.execute("SELECT id, case_id, original_filename, SUBSTR(extracted_content, 1, 200) as preview FROM evidence_items_v2 WHERE extracted_content LIKE '%博凯%' OR extracted_content LIKE '%升华%' LIMIT 10")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条")

# 列出案件1的所有证据
print("\n" + "=" * 60)
print("案件1的所有证据文件 (前20个):")
cursor.execute("SELECT id, original_filename FROM evidence_items_v2 WHERE case_id = 1 ORDER BY original_filename LIMIT 20")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r['original_filename']}")

# 看看有没有其他数据库文件包含博凯数据
print("\n" + "=" * 60)
print("检查其他数据库...")

# 检查项目表
cursor.execute("SELECT * FROM projects WHERE name LIKE '%博凯%' OR name LIKE '%升华%' LIMIT 10")
rows = cursor.fetchall()
print(f"projects 表中找到: {len(rows)} 条")

conn.close()