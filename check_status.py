import sqlite3
conn = sqlite3.connect(r'D:\www\法律大模型\legal_system.db')
cursor = conn.cursor()
cursor.execute('SELECT id, status FROM cases')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Status: {row[1]}")
conn.close()
