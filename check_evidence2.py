import sys
sys.path.insert(0, '.')
import app.models
from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check all records
    all_files = db.execute(text(
        "SELECT id, file_name, file_hash, status, evidence_id FROM evidence_folder_files ORDER BY id"
    )).fetchall()
    
    print(f'Total records in DB: {len(all_files)}')
    
    # Check for duplicate file names
    dup_names = db.execute(text(
        "SELECT file_name, COUNT(*) as cnt FROM evidence_folder_files GROUP BY file_name HAVING cnt > 1"
    )).fetchall()
    if dup_names:
        print(f'\nDuplicate file names ({len(dup_names)}):')
        for name, cnt in dup_names:
            print(f'  {name}: {cnt} times')
    
    # Check for duplicate hashes
    dup_hashes = db.execute(text(
        "SELECT file_hash, COUNT(*) as cnt FROM evidence_folder_files WHERE file_hash != '' GROUP BY file_hash HAVING cnt > 1"
    )).fetchall()
    if dup_hashes:
        print(f'\nDuplicate file hashes ({len(dup_hashes)}):')
        for h, cnt in dup_hashes[:5]:
            print(f'  {h[:20]}...: {cnt} times')
    
    # Check evidence links
    linked = db.execute(text(
        "SELECT COUNT(*) FROM evidence_folder_files WHERE evidence_id IS NOT NULL"
    )).fetchone()[0]
    not_linked = db.execute(text(
        "SELECT COUNT(*) FROM evidence_folder_files WHERE evidence_id IS NULL"
    )).fetchone()[0]
    print(f'\nLinked to evidence: {linked}')
    print(f'Not linked: {not_linked}')
    
    # Show first few unlinked files
    unlinked = db.execute(text(
        "SELECT file_name, status FROM evidence_folder_files WHERE evidence_id IS NULL LIMIT 5"
    )).fetchall()
    if unlinked:
        print('Unlinked files:')
        for name, status in unlinked:
            print(f'  {name}: {status}')
            
finally:
    db.close()
