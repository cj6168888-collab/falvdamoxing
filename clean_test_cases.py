import sqlite3
import os

db_path = r'D:\www\法律大模型\legal_system.db'

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看所有案件
cursor.execute('SELECT id, title, case_type FROM cases')
rows = cursor.fetchall()

print("当前所有案件:")
for r in rows:
    print(f"  ID: {r[0]}, 标题: {r[1]}, 类型: {r[2]}")

# 保留"博凯升华股东纠纷"，删除其他
cursor.execute('SELECT id FROM cases WHERE title != ?', ('博凯升华股东纠纷',))
to_delete = cursor.fetchall()

if to_delete:
    ids = [row[0] for row in to_delete]
    print(f"\n将删除 {len(ids)} 个案件: {ids}")
    
    # 安全删除 - 只删除存在的表
    tables_to_check = [
        'documents', 'generated_documents', 'document_suggestions',
        'adversarial_analysis', 'hearing_records', 'meeting_records',
        'case_structure', 'evidence_graph', 'letters', 'case_threads',
        'parties', 'counter_claims', 'evidence'
    ]
    
    for case_id in ids:
        for table in tables_to_check:
            try:
                cursor.execute(f'DELETE FROM {table} WHERE case_id = ?', (case_id,))
            except:
                pass  # 表不存在或无此字段
        
        # 最后删除案件
        try:
            cursor.execute('DELETE FROM cases WHERE id = ?', (case_id,))
        except:
            pass
    
    conn.commit()
    print("删除完成!")
else:
    print("\n没有需要删除的案件")

# 验证结果
cursor.execute('SELECT id, title, case_type FROM cases')
remaining = cursor.fetchall()
print(f"\n剩余案件 ({len(remaining)} 个):")
for r in remaining:
    print(f"  ID: {r[0]}, 标题: {r[1]}, 类型: {r[2]}")

conn.close()
