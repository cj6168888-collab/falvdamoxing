import sqlite3

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 检查 evidence_items_v2 表结构
print("=" * 60)
print("evidence_items_v2 表结构:")
cursor.execute("PRAGMA table_info(evidence_items_v2)")
for col in cursor.fetchall():
    print(f"  {col['name']}: {col['type']}")

# 查看案件列表
print("\n" + "=" * 60)
print("所有案件列表 (前20条):")
cursor.execute("SELECT id, title, case_number FROM cases ORDER BY id DESC LIMIT 20")
rows = cursor.fetchall()
for r in rows:
    print(f"  ID: {r['id']}, Title: {r['title']}")

# 查看证据Items_v2内容
print("\n" + "=" * 60)
print("evidence_items_v2 样例:")
cursor.execute("SELECT * FROM evidence_items_v2 LIMIT 3")
rows = cursor.fetchall()
for r in rows:
    d = dict(r)
    print(f"  {d}")

# 搜索证据的案件ID
print("\n" + "=" * 60)
print("搜索证据关联的案件...")
cursor.execute("SELECT DISTINCT case_id FROM evidence_items_v2 LIMIT 10")
rows = cursor.fetchall()
print(f"有证据的案件ID: {[r['case_id'] for r in rows]}")

# 查看项目列表
print("\n" + "=" * 60)
print("所有项目列表 (前20条):")
cursor.execute("SELECT id, name FROM projects ORDER BY id DESC LIMIT 20")
rows = cursor.fetchall()
for r in rows:
    print(f"  ID: {r['id']}, Name: {r['name']}")

conn.close()