# -*- coding: utf-8 -*-
"""数据库迁移脚本 - 添加缺失的case_direction列"""
import sys
sys.path.insert(0, 'd:/www/法律大模型')

from app.db.database import engine
from sqlalchemy import text

def migrate():
    print('Starting database migration...')
    try:
        with engine.connect() as conn:
            # 检查cases表的列
            result = conn.execute(text('PRAGMA table_info(cases)'))
            columns = [row[1] for row in result]
            print('Current columns:', columns)
            
            if 'case_direction' not in columns:
                print('Adding case_direction column...')
                conn.execute(text('ALTER TABLE cases ADD COLUMN case_direction VARCHAR(50) DEFAULT "mediate"'))
                conn.commit()
                print('[OK] Column case_direction added successfully')
            else:
                print('[SKIP] Column case_direction already exists')
                
    except Exception as e:
        print('Migration error:', str(e))
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    migrate()
