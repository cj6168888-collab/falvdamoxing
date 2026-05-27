import sqlite3

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 检查 cases 表结构
print("=" * 60)
print("cases 表结构:")
cursor.execute("PRAGMA table_info(cases)")
for col in cursor.fetchall():
    print(f"  {col['name']}: {col['type']}")

# 检查 evidence_items 表结构
print("\n" + "=" * 60)
print("evidence_items 表结构:")
cursor.execute("PRAGMA table_info(evidence_items)")
for col in cursor.fetchall():
    print(f"  {col['name']}: {col['type']}")

# 检查 projects 表结构
print("\n" + "=" * 60)
print("projects 表结构:")
cursor.execute("PRAGMA table_info(projects)")
for col in cursor.fetchall():
    print(f"  {col['name']}: {col['type']}")

# 搜索博凯案件
print("\n" + "=" * 60)
print("搜索 '博凯' 案件...")
cursor.execute("SELECT * FROM cases WHERE title LIKE '%博凯%'")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条案件")
for r in rows:
    print(f"  ID: {r['id']}, Title: {r['title']}, CaseNo: {r.get('case_no', 'N/A')}")

# 检查证据数量
print("\n" + "=" * 60)
print("证据统计...")
cursor.execute("SELECT COUNT(*) as cnt FROM evidence_items")
row = cursor.fetchone()
print(f"evidence_items 表: {row['cnt']} 条")

cursor.execute("SELECT COUNT(*) as cnt FROM evidence_items_v2")
row = cursor.fetchone()
print(f"evidence_items_v2 表: {row['cnt']} 条")

# 看看博凯案件的证据
if rows:
    case_id = rows[0]['id']
    print(f"\n" + "=" * 60)
    print(f"案件 {case_id} 的证据...")
    cursor.execute("SELECT COUNT(*) as cnt FROM evidence_items WHERE case_id = ?", (case_id,))
    row = cursor.fetchone()
    print(f"证据数量: {row['cnt']}")
    
    cursor.execute("SELECT * FROM evidence_items WHERE case_id = ? LIMIT 5", (case_id,))
    rows = cursor.fetchall()
    print("\n前5条证据:")
    for r in rows:
        print(f"  ID: {r['id']}, Title: {r['title']}, Type: {r.get('evidence_type', 'N/A')}")

conn.close()