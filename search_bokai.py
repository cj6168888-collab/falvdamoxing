import sqlite3

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 搜索所有包含"博凯"的记录
print("=" * 60)
print("搜索 '博凯' 在各个表中...")

# cases 表
print("\n--- cases 表 ---")
cursor.execute("SELECT id, title, case_number FROM cases WHERE title LIKE '%博凯%' OR title LIKE '%升华%'")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条案件")
for r in rows:
    print(f"  ID: {r['id']}, Title: {r['title']}, CaseNo: {r.get('case_number', 'N/A')}")

# projects 表
print("\n--- projects 表 ---")
cursor.execute("SELECT id, name FROM projects WHERE name LIKE '%博凯%' OR name LIKE '%升华%'")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条项目")
for r in rows:
    print(f"  ID: {r['id']}, Name: {r['name']}")

# evidence_items_v2 表
print("\n--- evidence_items_v2 表 ---")
cursor.execute("SELECT COUNT(*) as cnt FROM evidence_items_v2")
row = cursor.fetchone()
print(f"总记录数: {row['cnt']}")

# 搜索包含博凯或升华的证据
cursor.execute("SELECT * FROM evidence_items_v2 WHERE name LIKE '%博凯%' OR name LIKE '%升华%' LIMIT 10")
rows = cursor.fetchall()
print(f"包含 '博凯' 或 '升华' 的证据: {len(rows)} 条")
for r in rows:
    print(f"  ID: {r['id']}, Name: {r['name']}")

# 查看案件列表
print("\n" + "=" * 60)
print("所有案件列表 (前20条):")
cursor.execute("SELECT id, title, case_number FROM cases ORDER BY id DESC LIMIT 20")
rows = cursor.fetchall()
for r in rows:
    print(f"  ID: {r['id']}, Title: {r['title']}")

conn.close()