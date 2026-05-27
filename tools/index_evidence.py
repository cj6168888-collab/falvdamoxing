"""
将现有文档索引为证据的脚本
"""
import sqlite3
import uuid
from datetime import datetime

conn = sqlite3.connect(r'D:\www\法律大模型\legal_system.db')
conn.text_factory = str
cursor = conn.cursor()

print("=" * 60)
print("Indexing Documents as Evidence")
print("=" * 60)

# Check evidence_items_v2 schema
print("\nChecking schema...")
cursor.execute("PRAGMA table_info(evidence_items_v2)")
columns = cursor.fetchall()
col_names = [c[1] for c in columns]
print(f"Columns: {col_names}")

# Get all documents for case 21
print("\nFetching documents for case 21...")
cursor.execute("""
    SELECT id, filename, stored_path, file_type, content, content_summary, doc_type
    FROM documents WHERE case_id = 21
""")
documents = cursor.fetchall()
print(f"Found {len(documents)} documents")

# Check if evidence_items_v2 already has entries for case 21
cursor.execute("SELECT COUNT(*) FROM evidence_items_v2 WHERE case_id = 21")
existing_count = cursor.fetchone()[0]
print(f"Existing evidence items: {existing_count}")

if existing_count > 0:
    print("\nEvidence items already exist for case 21. Skipping indexing.")
    print("To re-index, delete existing evidence items first.")
else:
    print("\nIndexing documents as evidence...")
    
    indexed_count = 0
    for doc in documents:
        doc_id, filename, stored_path, file_type, content, content_summary, doc_type = doc
        
        # Determine source party
        if "对方" in (doc_type or "") or "被告" in (doc_type or ""):
            source_party = "opp"  # opponent
        elif "法院" in (doc_type or "") or "裁定" in (doc_type or ""):
            source_party = "court"  # court
        else:
            source_party = "our"  # our side
        
        # Determine evidence type
        if "合同" in (doc_type or "") or "协议" in (doc_type or ""):
            evidence_type = "CONTRACT"
        elif "支付" in (doc_type or "") or "转账" in (doc_type or "") or "银行" in (doc_type or ""):
            evidence_type = "PAYMENT"
        elif "身份" in (doc_type or "") or "执照" in (doc_type or "") or "证书" in (doc_type or ""):
            evidence_type = "IDENTITY"
        elif "函" in (doc_type or "") or "通知" in (doc_type or "") or "催告" in (doc_type or ""):
            evidence_type = "CORRESPONDENCE"
        elif "鉴定" in (doc_type or "") or "评估" in (doc_type or ""):
            evidence_type = "EXPERT"
        elif "视听" in (doc_type or "") or "录音" in (doc_type or "") or "录像" in (doc_type or ""):
            evidence_type = "AUDIO_VIDEO"
        elif "证言" in (doc_type or "") or "证人" in (doc_type or ""):
            evidence_type = "TESTIMONY"
        else:
            evidence_type = "DOCUMENT"
        
        # Prepare content
        raw_content = str(content)[:10000] if content else ""
        extracted_content = str(content) if content else ""
        summary = str(content_summary)[:500] if content_summary else filename
        
        # Create evidence item
        evidence_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute("""
                INSERT INTO evidence_items_v2 (
                    id, case_id, source_type, original_filename, file_path,
                    raw_content, extracted_content, summary,
                    evidence_type, source_party, status,
                    credibility_score, authenticity_score, reliability_score,
                    consistency_score, corroboration_score,
                    is_current, version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence_id,
                21,  # case_id
                "file",
                filename,
                stored_path,
                raw_content,
                extracted_content,
                summary,
                evidence_type,
                source_party,
                "indexed",
                0.0,  # credibility_score
                0.0,  # authenticity_score
                0.0,  # reliability_score
                0.0,  # consistency_score
                0.0,  # corroboration_score
                1,    # is_current
                1,    # version
                now,
                now
            ))
            indexed_count += 1
            print(f"  [{indexed_count}] Indexed: {filename[:50]}... as {evidence_type}")
        except Exception as e:
            print(f"  ERROR indexing {filename}: {e}")
    
    conn.commit()
    print(f"\nIndexed {indexed_count} documents as evidence")

# Verify
cursor.execute("SELECT COUNT(*) FROM evidence_items_v2 WHERE case_id = 21")
final_count = cursor.fetchone()[0]
print(f"\nFinal evidence count for case 21: {final_count}")

# Show sample
print("\nSample evidence items:")
cursor.execute("""
    SELECT id, original_filename, evidence_type, source_party, created_at
    FROM evidence_items_v2 WHERE case_id = 21 LIMIT 5
""")
samples = cursor.fetchall()
for s in samples:
    print(f"  - {s[2]}: {s[1][:40]}... ({s[3]})")

conn.close()
print("\n" + "=" * 60)
print("Indexing Complete")
print("=" * 60)
