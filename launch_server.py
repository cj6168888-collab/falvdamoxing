import sys
import os

# Set project root
project_root = r'D:\www\法律大模型'
os.chdir(project_root)
sys.path.insert(0, project_root)

# Start uvicorn
import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
