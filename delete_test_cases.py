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
    # 查看当前所有案件
    result = conn.execute(text("SELECT id, title FROM cases"))
    rows = result.fetchall()
    print("当前所有案件:")
    for row in rows:
        print(f"  ID {row[0]}: {row[1]}")
    
    # 删除除了案件1之外的所有案件
    print("\n正在删除测试案件...")
    result = conn.execute(text("DELETE FROM cases WHERE id != 1"))
    conn.commit()
    print(f"已删除 {result.rowcount} 条测试案件记录")
    
    # 验证结果
    result = conn.execute(text("SELECT id, title FROM cases"))
    rows = result.fetchall()
    print("\n删除后剩余案件:")
    for row in rows:
        print(f"  ID {row[0]}: {row[1]}")

print("\n✅ 清理完成！")