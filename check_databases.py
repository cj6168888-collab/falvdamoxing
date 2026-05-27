import sqlite3

# 检查 legal_system.db
print("=" * 60)
print("检查 legal_system.db (48MB)...")
conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查看所有表
print("\n表列表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for t in tables:
    print(f"  - {t[0]}")

# 搜索博凯
print("\n" + "=" * 60)
print("搜索 '博凯'...")
for table in ['projects', 'cases', 'evidence']:
    try:
        # 尝试 name 或 title 字段
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE name LIKE '%博凯%' OR title LIKE '%博凯%'")
        row = cursor.fetchone()
        print(f"{table} 表中找到: {row['cnt']} 条")
    except Exception as e:
        print(f"{table} 表: {e}")

# 检查 evidence 表总记录
try:
    cursor.execute("SELECT COUNT(*) as cnt FROM evidence")
    row = cursor.fetchone()
    print(f"\nevidence 表总记录数: {row['cnt']}")
    
    # 看看前几条证据
    cursor.execute("SELECT * FROM evidence LIMIT 3")
    rows = cursor.fetchall()
    print("\n证据表样例:")
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f"evidence 表: {e}")

conn.close()

print("\n" + "=" * 60)
print("检查 data/law_assistant.db (86KB)...")
conn2 = sqlite3.connect('d:/www/法律大模型/data/law_assistant.db')
conn2.row_factory = sqlite3.Row
cursor2 = conn2.cursor()

cursor2.execute("SELECT COUNT(*) as cnt FROM evidence")
row = cursor2.fetchone()
print(f"evidence 表总记录数: {row['cnt']}")

cursor2.execute("SELECT COUNT(*) as cnt FROM projects")
row = cursor2.fetchone()
print(f"projects 表总记录数: {row['cnt']}")

cursor2.execute("SELECT COUNT(*) as cnt FROM cases")
row = cursor2.fetchone()
print(f"cases 表总记录数: {row['cnt']}")

conn2.close()