from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl
import os
import uuid
import json
from typing import Optional, List, Dict
from datetime import datetime

from download_service import DownloadService, DownloadTask

app = FastAPI(title="Video Downloader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

download_service = DownloadService(DOWNLOAD_DIR)

class VideoInfoRequest(BaseModel):
    url: str
    proxy: Optional[str] = None

class DownloadRequest(BaseModel):
    url: str
    format_id: Optional[str] = None
    quality: Optional[str] = "best"
    filename: Optional[str] = None
    proxy: Optional[str] = None

class VideoFormat(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None

class VideoInfoResponse(BaseModel):
    title: str
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    uploader: Optional[str] = None
    formats: List[VideoFormat]
    webpage_url: str
    extractor: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "video-downloader-api"}

@app.get("/")
def root():
    return {"message": "Video Downloader API", "version": "1.0.0"}

@app.post("/api/info", response_model=VideoInfoResponse)
def get_video_info(request: VideoInfoRequest):
    try:
        info = download_service.get_info(request.url, proxy=request.proxy)
        formats = []
        for f in info.get("formats", []):
            formats.append(VideoFormat(
                format_id=f.get("format_id", ""),
                ext=f.get("ext", ""),
                resolution=f.get("resolution"),
                filesize=f.get("filesize"),
                vcodec=f.get("vcodec"),
                acodec=f.get("acodec"),
            ))
        return VideoInfoResponse(
            title=info.get("title", "Unknown"),
            duration=info.get("duration"),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("uploader"),
            formats=formats,
            webpage_url=info.get("webpage_url", request.url),
            extractor=info.get("extractor", "unknown"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    try:
        task = download_service.create_task(
            task_id=task_id,
            url=request.url,
            format_id=request.format_id,
            quality=request.quality,
            filename=request.filename,
            proxy=request.proxy,
        )
        background_tasks.add_task(download_service.download, task)
        return {"task_id": task_id, "status": "started", "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download/{task_id}")
def get_download_status(task_id: str):
    task = download_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()

@app.get("/api/downloads")
def list_downloads():
    return [task.to_dict() for task in download_service.get_all_tasks()]

@app.get("/api/download/{task_id}/file")
def download_file(task_id: str):
    task = download_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Download not completed")
    if not os.path.exists(task.filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = os.path.basename(task.filepath)
    return FileResponse(
        task.filepath,
        media_type="application/octet-stream",
        filename=filename,
    )

@app.delete("/api/download/{task_id}")
def delete_download(task_id: str):
    task = download_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    download_service.delete_task(task_id)
    return {"message": "Task deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
