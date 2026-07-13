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
    status: str = "pending"  # pending, downloading, paused, completed, error, stopping
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
    has_audio: bool = True

    # Threading controls (not serialized)
    _pause_event: threading.Event = field(default_factory=threading.Event, repr=False, compare=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, repr=False, compare=False)
    _thread: Optional[threading.Thread] = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        # Ensure events are set on unpickling/copying
        if self._pause_event is None:
            self._pause_event = threading.Event()
        if self._stop_event is None:
            self._stop_event = threading.Event()
        # pause_event.set() means NOT paused (running)
        self._pause_event.set()

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
            "has_audio": self.has_audio,
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

    def create_task(
        self,
        task_id: str,
        url: str,
        format_id: Optional[str] = None,
        quality: str = "best",
        filename: Optional[str] = None,
        proxy: Optional[str] = None,
        has_audio: bool = True,
    ) -> DownloadTask:
        task = DownloadTask(
            task_id=task_id,
            url=url,
            format_id=format_id,
            quality=quality,
            proxy=proxy,
            has_audio=has_audio,
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
        if task:
            self._stop_task(task)
        if task and task.filepath and os.path.exists(task.filepath):
            try:
                os.remove(task.filepath)
            except Exception:
                pass

    def pause_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        if task.status not in ("pending", "downloading"):
            return False
        task._pause_event.clear()  # clear = PAUSED
        task.status = "paused"
        return True

    def resume_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        if task.status != "paused":
            return False
        task._pause_event.set()  # set = RUNNING
        task.status = "downloading"
        return True

    def restart_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        if task.status in ("pending", "downloading", "paused"):
            self._stop_task(task)

        # Reset task state
        task.status = "pending"
        task.progress = 0.0
        task.error_message = None
        task.retry_count = 0
        task.completed_at = None
        task._pause_event.set()
        task._stop_event.clear()
        task._thread = None

        # Start fresh download thread
        self._start_download_thread(task)
        return True

    def _stop_task(self, task: DownloadTask):
        """Request thread stop and wait for it."""
        task._stop_event.set()
        task._pause_event.set()  # Unblock if paused
        task.status = "stopping"
        if task._thread and task._thread.is_alive():
            task._thread.join(timeout=10)

    def download(self, task: DownloadTask):
        """Public entry point — starts download in a background thread."""
        self._start_download_thread(task)

    def _start_download_thread(self, task: DownloadTask):
        thread = threading.Thread(target=self._download_worker, args=(task,), daemon=True)
        task._thread = thread
        task.status = "downloading"
        thread.start()

    def _progress_hook(self, task: DownloadTask):
        def hook(d):
            # Check stop request
            if task._stop_event.is_set():
                raise Exception("Stop requested by user")

            # Check pause
            if not task._pause_event.is_set():
                task.status = "paused"
                task._pause_event.wait()  # Block until resumed
                if task._stop_event.is_set():
                    raise Exception("Stop requested by user")
                task.status = "downloading"

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
        outtmpl = os.path.join(self.download_dir, f"{task.task_id}_%(title)s.%(ext)s")

        opts = {
            "outtmpl": outtmpl,
            "progress_hooks": [self._progress_hook(task)],
            "quiet": True,
            "no_warnings": True,
            # ---- FFmpeg location (bundled) ----
            "ffmpeg_location": os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg", "ffmpeg.exe"),
            # ---- Retry & Resume settings ----
            "retries": 10,
            "fragment_retries": 10,
            "continue_dl": True,
            "nopart": False,
            "extractor_retries": 5,
            # ---- Timeout & buffering ----
            "socket_timeout": 60,
            "buffersize": 65536,
            # ---- Parallel downloads ----
            "concurrent_fragment_downloads": 3,
            # ---- User agent ----
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        if task.format_id:
            # If format has no audio, automatically merge with best audio
            if not task.has_audio:
                opts["format"] = f"{task.format_id}+bestaudio/best"
                opts["merge_output_format"] = "mp4"
                opts["postprocessors"] = [{"key": "FFmpegMerger", "preferedformat": "mp4"}]
            else:
                opts["format"] = task.format_id
        else:
            opts["format"] = task.quality

        if task.proxy:
            opts["proxy"] = task.proxy

        return opts

    def _download_worker(self, task: DownloadTask):
        """Actual download worker running in a thread."""
        last_error = None

        while task.retry_count <= task.max_retries:
            # Check stop at loop start
            if task._stop_event.is_set():
                task.status = "error"
                task.error_message = "Остановлено пользователем"
                task.completed_at = datetime.now().isoformat()
                return

            try:
                task.status = "downloading"
                task.error_message = None

                if task.retry_count > 0:
                    delay = min(2 ** task.retry_count, 30)
                    time.sleep(delay)

                ydl_opts = self._build_ydl_opts(task)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(task.url, download=True)
                    task.title = info.get("title")

                    actual_filename = ydl.prepare_filename(info)
                    if os.path.exists(actual_filename):
                        task.filepath = actual_filename
                        task.filename = os.path.basename(actual_filename)
                    else:
                        for ext in ["mp4", "webm", "mkv", "m4a", "mp3"]:
                            alt = actual_filename.rsplit(".", 1)[0] + f".{ext}"
                            if os.path.exists(alt):
                                task.filepath = alt
                                task.filename = os.path.basename(alt)
                                break

                task.status = "completed"
                task.progress = 100.0
                task.completed_at = datetime.now().isoformat()
                return

            except Exception as e:
                # Stop requested — don't retry
                if task._stop_event.is_set():
                    task.status = "error"
                    task.error_message = "Остановлено пользователем"
                    task.completed_at = datetime.now().isoformat()
                    return

                last_error = str(e)
                task.retry_count += 1
                task.error_message = f"Попытка {task.retry_count}/{task.max_retries + 1}: {last_error}"

                if task.retry_count > task.max_retries:
                    task.status = "error"
                    task.error_message = f"Все попытки исчерпаны. Последняя ошибка: {last_error}"
                    task.completed_at = datetime.now().isoformat()
                    return

                time.sleep(1)
