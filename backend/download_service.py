import yt_dlp
import os
import threading
import time
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
    retry_count: int = 0
    max_retries: int = 3
    proxy: Optional[str] = None
    
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
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "proxy": self.proxy,
        }

class DownloadService:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        self.tasks: Dict[str, DownloadTask] = {}
        self._lock = threading.Lock()
        os.makedirs(download_dir, exist_ok=True)
    
    def get_info(self, url: str, proxy: Optional[str] = None) -> Dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        if proxy:
            ydl_opts["proxy"] = proxy
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    
    def create_task(self, task_id: str, url: str, format_id: Optional[str] = None, 
                    quality: str = "best", filename: Optional[str] = None,
                    proxy: Optional[str] = None) -> DownloadTask:
        task = DownloadTask(
            task_id=task_id,
            url=url,
            format_id=format_id,
            quality=quality,
            proxy=proxy,
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
    
    def _build_ydl_opts(self, task: DownloadTask) -> Dict:
        """Build yt-dlp options with retries, resume, and timeout settings."""
        outtmpl = os.path.join(self.download_dir, f"{task.task_id}_%(title)s.%(ext)s")
        
        opts = {
            "outtmpl": outtmpl,
            "progress_hooks": [self._progress_hook(task)],
            "quiet": True,
            "no_warnings": True,
            # ---- Retry & Resume settings ----
            "retries": 10,                          # 10 retries on network errors
            "fragment_retries": 10,                 # 10 retries per video fragment
            "continue_dl": True,                    # RESUME downloads (partial files)
            "nopart": False,                        # use .part files for resume
            "extractor_retries": 5,                 # retries for info extraction
            # ---- Timeout & buffering ----
            "socket_timeout": 60,                   # 60 seconds socket timeout
            "buffersize": 65536,                    # 64KB buffer
            # ---- Parallel downloads ----
            "concurrent_fragment_downloads": 3,     # download 3 fragments at once
            # ---- User agent (helps avoid blocks) ----
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        
        if task.format_id:
            opts["format"] = task.format_id
        else:
            opts["format"] = task.quality
        
        if task.proxy:
            opts["proxy"] = task.proxy
            
        return opts
    
    def download(self, task: DownloadTask):
        """Download with automatic retries and resume support."""
        last_error = None
        
        while task.retry_count <= task.max_retries:
            try:
                task.status = "downloading"
                task.error_message = None
                if task.retry_count > 0:
                    # Add delay between retries (exponential backoff)
                    delay = min(2 ** task.retry_count, 30)
                    time.sleep(delay)
                
                ydl_opts = self._build_ydl_opts(task)
                
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
                return  # Success — exit retry loop
                
            except Exception as e:
                last_error = str(e)
                task.retry_count += 1
                task.error_message = f"Попытка {task.retry_count}/{task.max_retries + 1}: {last_error}"
                
                # If max retries reached, mark as error
                if task.retry_count > task.max_retries:
                    task.status = "error"
                    task.error_message = f"Все попытки исчерпаны. Последняя ошибка: {last_error}"
                    task.completed_at = datetime.now().isoformat()
                    return
                
                # Otherwise, loop will retry
                # Small delay before next attempt
                time.sleep(1)
