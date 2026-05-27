import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('d:/www/法律大模型/legal_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("搜索证据内容包含 '博凯' 或 '升华' 的证据...")
cursor.execute("""
    SELECT id, case_id, original_filename, 
           SUBSTR(extracted_content, 1, 500) as preview
    FROM evidence_items_v2 
    WHERE extracted_content LIKE '%博凯%' OR extracted_content LIKE '%升华%'
    LIMIT 10
""")
rows = cursor.fetchall()
print(f"找到 {len(rows)} 条包含关键词的证据")

for r in rows:
    print(f"\n证据 ID: {r['id']}")
    print(f"  文件名: {r['original_filename']}")
    print(f"  案件ID: {r['case_id']}")
    print(f"  内容预览: {r['preview'][:200]}...")

print("\n" + "=" * 60)
print("所有证据的案件分布:")
cursor.execute("SELECT case_id, COUNT(*) as cnt FROM evidence_items_v2 GROUP BY case_id")
rows = cursor.fetchall()
for r in rows:
    print(f"  案件ID {r['case_id']}: {r['cnt']} 条证据")

# 检查案件1的所有证据文件名
print("\n" + "=" * 60)
print("案件1的所有证据文件名 (前30个):")
cursor.execute("SELECT original_filename FROM evidence_items_v2 WHERE case_id = 1 ORDER BY original_filename")
rows = cursor.fetchall()
for i, r in enumerate(rows[:30]):
    print(f"  {i+1}. {r['original_filename']}")

conn.close()