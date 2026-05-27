# ============ 文件上传分析 API (临时调试版) ============
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter(prefix="/api/smart-chat", tags=["智能对话分析"])

@router.post("/upload-analysis")
async def upload_file_analysis(
    case_id: int = Form(...),
    user_message: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    print(f"[upload-analysis] SIMPLE TEST - case_id={case_id}, file={file.filename}")
    return {
        "analysis_id": 999,
        "content": "文件上传测试成功",
        "message": f"收到文件: {file.filename}"
    }