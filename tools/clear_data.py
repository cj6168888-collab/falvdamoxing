"""
清理测试数据脚本
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

def clear_database(db_path, db_name):
    print(f"\n{'='*50}")
    print(f"清空 {db_name}")
    print('='*50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查看表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"表: {tables}")
    
    # 需要保留的表（模板、系统配置等）
    protected = ['users', 'system_config', 'template']
    
    for table in tables:
        if table in protected:
            print(f"  [保留] {table}")
            continue
            
        try:
            cursor.execute(f"DELETE FROM {table}")
            count = cursor.rowcount
            if count > 0:
                print(f"  [删除] {table}: {count} 条")
        except Exception as e:
            print(f"  [跳过] {table}: {e}")
    
    conn.commit()
    conn.close()
    print(f"{db_name} 清理完成")

# 清空主数据库
clear_database('legal_system.db', '主数据库')

# 清空 UI 数据库
clear_database('ui/legal_system.db', 'UI数据库')

# 清空向量数据库
try:
    import shutil
    chroma_path = 'data/chroma'
    if shutil.os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)
        print(f"\n[删除] 向量数据库已清空: {chroma_path}")
except Exception as e:
    print(f"向量数据库清理: {e}")

print("\n" + "="*50)
print("所有测试数据已清空！")
print("="*50)
