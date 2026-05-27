import sqlite3

conn = sqlite3.connect('legal_system.db')
cursor = conn.cursor()

# 检查表结构
cursor.execute("PRAGMA table_info(evidence_items_v2)")
columns = [row[1] for row in cursor.fetchall()]

# 需要添加的列
missing_cols = {
    'display_name': 'TEXT',
    'evidence_number': 'TEXT',
    'search_keywords': 'TEXT',
    'related_claims': 'TEXT',
    'user_corrections': 'TEXT',
    'ai_corrections_acknowledged': 'INTEGER DEFAULT 0',
    'usage_direction': 'TEXT',
    'usage_annotations': 'TEXT',
    'usage_tags': 'TEXT',
    'is_highlighted': 'INTEGER DEFAULT 0',
    'highlight_reason': 'TEXT',
    'safety_level': 'TEXT DEFAULT safe',
    'safety_warnings': 'TEXT',
    'adverse_impact_analysis': 'TEXT',
    'is_warning_ignored': 'INTEGER DEFAULT 0',
    'ignored_reason': 'TEXT',
    'safety_reviewed': 'INTEGER DEFAULT 0',
    'safety_reviewed_by': 'TEXT',
    'safety_reviewed_at': 'TIMESTAMP',
}

for col, col_type in missing_cols.items():
    if col not in columns:
        try:
            cursor.execute(f"ALTER TABLE evidence_items_v2 ADD COLUMN {col} {col_type}")
            print(f"Added column: {col}")
        except Exception as e:
            print(f"Error adding {col}: {e}")

conn.commit()
print("Done!")
conn.close()