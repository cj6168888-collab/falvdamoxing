import sys
sys.path.insert(0, '.')
import app.models
from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Delete all folder file records (they reference old file names)
    count = db.execute(text('DELETE FROM evidence_folder_files')).rowcount
    print(f'Deleted {count} folder file records')
    
    # Delete all evidence items
    count = db.execute(text('DELETE FROM evidence_items_v2')).rowcount
    print(f'Deleted {count} evidence items')
    
    # Delete all folder scans
    count = db.execute(text('DELETE FROM evidence_folder_scans')).rowcount
    print(f'Deleted {count} folder scan records')
    
    # Reset case folder config
    db.execute(text("UPDATE cases SET evidence_folder_path = NULL, evidence_folder_enabled = 0"))
    print('Reset case folder config')
    
    db.commit()
    print('Done')
finally:
    db.close()
