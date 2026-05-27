import uvicorn
import os
os.chdir(r'D:\www\法律大模型')
uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=False)
