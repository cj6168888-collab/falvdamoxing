import sys
sys.path.insert(0, 'd:/www/法律大模型')

from app.db.storage import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# 搜索项目
print("=" * 50)
print("搜索 projects 表中的 '博凯'...")
cursor.execute("SELECT * FROM projects WHERE name LIKE '%博凯%'")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条项目记录")
for r in rows:
    print(dict(r))

print("\n" + "=" * 50)
print("搜索 cases 表中的 '博凯'...")
cursor.execute("SELECT * FROM cases WHERE title LIKE '%博凯%'")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条案件记录")
for r in rows:
    print(dict(r))

print("\n" + "=" * 50)
print("搜索 evidence 表...")
cursor.execute("SELECT COUNT(*) as cnt FROM evidence")
row = cursor.fetchone()
print(f"证据表总记录数: {row['cnt']}")

# 搜索证据
print("\n搜索 evidence 表中的 '博凯'...")
cursor.execute("SELECT * FROM evidence WHERE title LIKE '%博凯%' LIMIT 10")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条证据记录")
for r in rows:
    print(dict(r))

conn.close()
print("\n查询完成!")