import sqlite3
import sys
import io

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查看证据关联的案件
print("=" * 60)
print("evidence_items_v2 证据关联的案件:")
cursor.execute("SELECT DISTINCT case_id, COUNT(*) as cnt FROM evidence_items_v2 GROUP BY case_id")
rows = cursor.fetchall()
for r in rows:
    print(f"  案件ID: {r['case_id']}, 证据数: {r['cnt']}")

# 查看案件详情
print("\n" + "=" * 60)
print("案件详情:")
cursor.execute("SELECT * FROM cases ORDER BY id DESC LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    print(f"  ID: {r['id']}, Title: {r['title']}")

# 查看证据样例
print("\n" + "=" * 60)
print("证据样例 (提取的文本前100字符):")
cursor.execute("SELECT id, case_id, original_filename, LENGTH(extracted_content) as content_len FROM evidence_items_v2 LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    content_len = r['content_len'] or 0
    print(f"  ID: {r['id']}, CaseID: {r['case_id']}, File: {r['original_filename']}, Content length: {content_len}")

conn.close()