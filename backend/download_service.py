import yt_dlp
import os
import threading
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DownloadTask:
    task_id: str
    url: str
    status: str = "pending"  # pending, downloading, completed, error
    progress: float = 0.0
    filename: Optional[str] = None
    filepath: Optional[str] = None
    format_id: Optional[str] = None
    quality: str = "best"
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    title: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "url": self.url,
            "status": self.status,
            "progress": self.progress,
            "filename": self.filename,
            "filepath": self.filepath,
            "format_id": self.format_id,
            "quality": self.quality,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "title": self.title,
        }

class DownloadService:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        self.tasks: Dict[str, DownloadTask] = {}
        self._lock = threading.Lock()
        os.makedirs(download_dir, exist_ok=True)
    
    def get_info(self, url: str) -> Dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    
    def create_task(self, task_id: str, url: str, format_id: Optional[str] = None, 
                    quality: str = "best", filename: Optional[str] = None) -> DownloadTask:
        task = DownloadTask(
            task_id=task_id,
            url=url,
            format_id=format_id,
            quality=quality,
        )
        with self._lock:
            self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[DownloadTask]:
        with self._lock:
            return list(self.tasks.values())
    
    def delete_task(self, task_id: str):
        with self._lock:
            task = self.tasks.pop(task_id, None)
        if task and task.filepath and os.path.exists(task.filepath):
            try:
                os.remove(task.filepath)
            except Exception:
                pass
    
    def _progress_hook(self, task: DownloadTask):
        def hook(d):
            if d["status"] == "downloading":
                task.status = "downloading"
                if "downloaded_bytes" in d and "total_bytes" in d and d["total_bytes"]:
                    task.progress = round(d["downloaded_bytes"] / d["total_bytes"] * 100, 2)
                elif "downloaded_bytes" in d and "total_bytes_estimate" in d and d["total_bytes_estimate"]:
                    task.progress = round(d["downloaded_bytes"] / d["total_bytes_estimate"] * 100, 2)
            elif d["status"] == "finished":
                task.progress = 100.0
        return hook
    
    def download(self, task: DownloadTask):
        try:
            task.status = "downloading"
            task.progress = 0.0
            
            outtmpl = os.path.join(self.download_dir, f"{task.task_id}_%(title)s.%(ext)s")
            
            ydl_opts = {
                "outtmpl": outtmpl,
                "progress_hooks": [self._progress_hook(task)],
                "quiet": True,
                "no_warnings": True,
            }
            
            if task.format_id:
                ydl_opts["format"] = task.format_id
            else:
                ydl_opts["format"] = task.quality
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(task.url, download=True)
                task.title = info.get("title")
                
                # Determine actual filename
                actual_filename = ydl.prepare_filename(info)
                if os.path.exists(actual_filename):
                    task.filepath = actual_filename
                    task.filename = os.path.basename(actual_filename)
                else:
                    # Try common extensions if prepare_filename didn't match
                    for ext in ["mp4", "webm", "mkv", "m4a", "mp3"]:
                        alt = actual_filename.rsplit(".", 1)[0] + f".{ext}"
                        if os.path.exists(alt):
                            task.filepath = alt
                            task.filename = os.path.basename(alt)
                            break
            
            task.status = "completed"
            task.progress = 100.0
            task.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            task.completed_at = datetime.now().isoformat()
