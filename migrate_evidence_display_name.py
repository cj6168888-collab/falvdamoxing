"""
为已有证据生成 display_name（规范显示名称）
使用原始 SQL 避免 SQLAlchemy 模型依赖问题
"""
import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'legal_system.db')

TYPE_NAMES = {
    'CONTRACT': '合同',
    'CORRESPONDENCE': '往来函件',
    'PAYMENT': '付款凭证',
    'IDENTITY': '主体资格',
    'AUDIO_VIDEO': '视听资料',
    'TESTIMONY': '证人证言',
    'EXPERT': '鉴定意见',
    'DOCUMENT': '书证',
    'ELECTRONIC': '电子数据',
    'PHOTO': '照片',
    'OTHER': '其他证据',
}

def clean_filename(name):
    if not name:
        return ''
    base = name.rsplit('.', 1)[0] if '.' in name else name
    for prefix in ['企业微信', '微信', '钉钉', 'QQ', '邮件', 'email_', 'IMG_', 'DOC_']:
        if base.startswith(prefix):
            base = base[len(prefix):]
            break
    return base[:15]

def generate_name(evidence_type, original_filename):
    type_name = TYPE_NAMES.get(evidence_type, '证据')
    base = clean_filename(original_filename)
    if base:
        return f"{type_name}-{base}"
    return type_name

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查 display_name 列是否存在
    cursor.execute("PRAGMA table_info(evidence_items_v2)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'display_name' not in columns:
        print("添加 display_name 列...")
        cursor.execute("ALTER TABLE evidence_items_v2 ADD COLUMN display_name VARCHAR(200)")
        conn.commit()
    
    # 查找没有 display_name 的证据
    cursor.execute("""
        SELECT id, original_filename, evidence_type 
        FROM evidence_items_v2 
        WHERE display_name IS NULL OR display_name = ''
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("所有证据已有 display_name，无需迁移")
        conn.close()
        return
    
    print(f"找到 {len(rows)} 个需要生成 display_name 的证据")
    
    updated = 0
    for row in rows:
        ev_id, original_filename, evidence_type = row
        display_name = generate_name(evidence_type, original_filename)
        cursor.execute(
            "UPDATE evidence_items_v2 SET display_name = ? WHERE id = ?",
            (display_name, ev_id)
        )
        updated += 1
        print(f"  [{updated}] {original_filename or '未命名'} -> {display_name}")
    
    conn.commit()
    conn.close()
    print(f"\n完成！更新了 {updated} 个证据的 display_name")

if __name__ == '__main__':
    migrate()
