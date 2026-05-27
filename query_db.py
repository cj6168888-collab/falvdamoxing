import sqlite3
import os

# Find database file - prefer legal_system.db
db_dir = r'd:\www\法律大模型'
db_path = None

# First try legal_system.db
for root, dirs, files in os.walk(db_dir):
    for f in files:
        if f == 'legal_system.db':
            db_path = os.path.join(root, f)
            break
    if db_path:
        break

# If not found, try any .db file
if not db_path:
    for root, dirs, files in os.walk(db_dir):
        for f in files:
            if f.endswith('.db'):
                db_path = os.path.join(root, f)
                break
        if db_path:
            break

if not db_path:
    print("数据库文件未找到!")
    exit(1)

print(f"找到数据库: {db_path}\n")

# Connect and query
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# First, list all tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("数据库中的表:")
for t in tables:
    print(f"  - {t[0]}")
print()

# Query 1: Count records
count_sql = """
SELECT COUNT(*) 
FROM documents 
WHERE case_id = 1 
AND (
    doc_type LIKE '%证据%' 
    OR doc_type LIKE '%合同%' 
    OR doc_type LIKE '%函件%' 
    OR doc_type LIKE '%协议%' 
    OR doc_type LIKE '%章程%'
)
"""
cursor.execute(count_sql)
total_count = cursor.fetchone()[0]
print(f"查询1: 符合条件(case_id=1且doc_type包含指定关键词)的记录总数: {total_count}")

# Query 2: Distribution by doc_type
dist_sql = """
SELECT doc_type, COUNT(*) as count 
FROM documents 
WHERE case_id = 1 
AND (
    doc_type LIKE '%证据%' 
    OR doc_type LIKE '%合同%' 
    OR doc_type LIKE '%函件%' 
    OR doc_type LIKE '%协议%' 
    OR doc_type LIKE '%章程%'
)
GROUP BY doc_type
ORDER BY count DESC
"""
cursor.execute(dist_sql)
results = cursor.fetchall()

print("\n查询2: doc_type 分布:")
print("-" * 50)
for row in results:
    print(f"  {row[0]}: {row[1]} 条")

conn.close()
