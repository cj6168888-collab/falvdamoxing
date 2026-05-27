import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir('d:/www/法律大模型')

from sqlalchemy import create_engine, text

db_path = "legal_system.db"
uri_db_url = f"sqlite:///{db_path}?charset=utf8"
engine = create_engine(uri_db_url, connect_args={"check_same_thread": False})

with engine.connect() as conn:
    # 更新案件1的标题
    result = conn.execute(text("UPDATE cases SET title = '博凯升华投资纠纷案' WHERE id = 1"))
    conn.commit()
    
    print(f"已更新 {result.rowcount} 条记录")
    
    # 验证更新
    result = conn.execute(text("SELECT id, title, plaintiff, defendant FROM cases WHERE id = 1"))
    row = result.fetchone()
    print(f"\n案件ID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"原告: {row[2]}")
    print(f"被告: {row[3]}")

print("\n✅ 更新完成！请刷新页面查看。")