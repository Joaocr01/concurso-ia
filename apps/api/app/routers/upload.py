from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from redis import Redis
import os
from ..schemas import UploadTextRequest

router = APIRouter()

def get_redis():
    return Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

@router.post("")
async def upload_text(req: UploadTextRequest, r: Redis = Depends(get_redis)):
    job = {
        "type": "text",
        "filename": req.filename,
        "content": req.content,
    }
    r.lpush("ingest_queue", str(job))
    return {"queued": True}

@router.post("/file")
async def upload_file(file: UploadFile = File(...), r: Redis = Depends(get_redis)):
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(400, "Apenas PDF ou TXT por enquanto.")
    content = await file.read()
    job = {
        "type": "pdf" if file.filename.lower().endswith(".pdf") else "text",
        "filename": file.filename,
        "content": content.decode("utf-8", errors="ignore") if file.filename.endswith(".txt") else None,
        "raw_bytes": content if file.filename.endswith(".pdf") else None,
    }
    r.lpush("ingest_queue", str(job))
    return {"queued": True}