import sys
sys.path.insert(0, '.')
import app.models
from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check status distribution
    results = db.execute(text(
        "SELECT status, COUNT(*) as cnt FROM evidence_folder_files GROUP BY status"
    )).fetchall()
    print('File status distribution:')
    for status, count in results:
        print(f'  {status}: {count}')
    
    total = db.execute(text('SELECT COUNT(*) FROM evidence_folder_files')).fetchone()[0]
    print(f'Total files in DB: {total}')
    
    # Check failed files
    failed = db.execute(text(
        "SELECT file_name, error_message FROM evidence_folder_files WHERE status='failed' LIMIT 10"
    )).fetchall()
    if failed:
        print(f'\nFailed files ({len(failed)} shown):')
        for name, err in failed:
            print(f'  {name}: {err[:100] if err else "no error"}')
    
    # Check skipped files
    skipped = db.execute(text(
        "SELECT file_name, error_message FROM evidence_folder_files WHERE status='skipped' LIMIT 10"
    )).fetchall()
    if skipped:
        print(f'\nSkipped files ({len(skipped)} shown):')
        for name, err in skipped:
            print(f'  {name}: {err[:100] if err else "no error"}')
    
    # Check pending files
    pending = db.execute(text(
        "SELECT file_name, status FROM evidence_folder_files WHERE status='pending' LIMIT 10"
    )).fetchall()
    if pending:
        print(f'\nPending files:')
        for name, status in pending:
            print(f'  {name}: {status}')
            
    # Check files with no evidence linked
    no_ev = db.execute(text(
        "SELECT file_name, status FROM evidence_folder_files WHERE evidence_id IS NULL LIMIT 10"
    )).fetchall()
    if no_ev:
        print(f'\nFiles without evidence link:')
        for name, status in no_ev:
            print(f'  {name}: {status}')
            
    # Count actual files on disk
    import os
    folder_path = r'D:\www\法律大模型\data\files\1'
    if os.path.exists(folder_path):
        all_files = []
        for f in os.listdir(folder_path):
            fp = os.path.join(folder_path, f)
            if os.path.isfile(fp):
                ext = os.path.splitext(f)[1].lower().lstrip('.')
                supported = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'txt', 'md', 'rtf'}
                if ext in supported:
                    all_files.append(f)
        print(f'\nActual files on disk: {len(all_files)}')
        print(f'Recognized in DB: {total}')
        print(f'Missing: {len(all_files) - total}')
finally:
    db.close()
