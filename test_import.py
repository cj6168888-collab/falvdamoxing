import sys
sys.path.insert(0, r'D:\www\法律大模型')
try:
    from app.main import app
    print("SUCCESS: App loaded")
    print(f"Routes: {len(app.routes)}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
