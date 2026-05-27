import os
os.chdir('d:/www/法律大模型')

from sqlalchemy import create_engine, text

# 使用与 app/config.py 相同的连接方式
db_path = "legal_system.db"
uri_db_url = f"sqlite:///{db_path}?charset=utf8"
print(f"Connecting to: {uri_db_url}")

engine = create_engine(uri_db_url, connect_args={"check_same_thread": False})

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, title, plaintiff, defendant FROM cases"))
    rows = result.fetchall()
    
    print("\nQuery results:")
    for row in rows:
        print(f"ID: {row[0]}, Title: {row[1]}, Plaintiff: {row[2]}, Defendant: {row[3]}")