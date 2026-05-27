import sqlite3

db_path = r'D:\www\法律大模型\legal_system.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 数据库检查 ===")

# 查看表结构
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%evidence%'")
tables = cursor.fetchall()
print("证据相关表:", [t[0] for t in tables])

for case_id in [1, 2, 3]:
    print(f"\n案件 {case_id}:")
    cursor.execute('SELECT title FROM cases WHERE id=?', (case_id,))
    row = cursor.fetchone()
    title = row[0] if row else "不存在"
    print(f"  案件名: {title}")
    
    # evidence_items_v2
    cursor.execute('SELECT COUNT(*) FROM evidence_items_v2 WHERE case_id=?', (case_id,))
    print(f"  证据v2: {cursor.fetchone()[0]}")
    
    # case_claims
    cursor.execute('SELECT COUNT(*) FROM case_claims WHERE case_id=?', (case_id,))
    print(f"  战役: {cursor.fetchone()[0]}")
    
    # generated_documents
    cursor.execute('SELECT COUNT(*) FROM generated_documents WHERE case_id=?', (case_id,))
    print(f"  生成文书: {cursor.fetchone()[0]}")

conn.close()
print("\n=== 完成 ===")