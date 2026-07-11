import { useState, useEffect } from 'react';
import { Trash2, Download, RefreshCw, Loader2, CheckCircle, XCircle, Clock, Pause, Play, RotateCcw } from 'lucide-react';

interface DownloadTask {
  task_id: string;
  url: string;
  status: string;
  progress: number;
  filename: string | null;
  title: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

const API_BASE = '/api';
const POLL_INTERVAL = 2000;

export default function DownloadList() {
  const [tasks, setTasks] = useState<DownloadTask[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_BASE}/downloads`);
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (e) {
      console.error('Failed to fetch tasks:', e);
    } finally {
      setLoading(false);
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      await fetch(`${API_BASE}/download/${taskId}`, { method: 'DELETE' });
      setTasks((prev) => prev.filter((t) => t.task_id !== taskId));
    } catch (e) {
      console.error('Failed to delete task:', e);
    }
  };

  const pauseTask = async (taskId: string) => {
    try {
      const res = await fetch(`${API_BASE}/download/${taskId}/pause`, { method: 'POST' });
      if (res.ok) fetchTasks();
    } catch (e) {
      console.error('Failed to pause task:', e);
    }
  };

  const resumeTask = async (taskId: string) => {
    try {
      const res = await fetch(`${API_BASE}/download/${taskId}/resume`, { method: 'POST' });
      if (res.ok) fetchTasks();
    } catch (e) {
      console.error('Failed to resume task:', e);
    }
  };

  const restartTask = async (taskId: string) => {
    try {
      const res = await fetch(`${API_BASE}/download/${taskId}/restart`, { method: 'POST' });
      if (res.ok) fetchTasks();
    } catch (e) {
      console.error('Failed to restart task:', e);
    }
  };

  const downloadFile = (taskId: string, filename: string) => {
    window.open(`${API_BASE}/download/${taskId}/file`, '_blank');
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const statusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'downloading': return <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />;
      case 'paused': return <Pause className="w-4 h-4 text-amber-400" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const statusText = (status: string) => {
    switch (status) {
      case 'pending': return 'В очереди';
      case 'downloading': return 'Загрузка...';
      case 'paused': return 'На паузе';
      case 'completed': return 'Готово';
      case 'error': return 'Ошибка';
      default: return status;
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-400';
      case 'downloading': return 'text-cyan-400';
      case 'paused': return 'text-amber-400';
      case 'completed': return 'text-emerald-400';
      case 'error': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  const progressColor = (status: string) => {
    switch (status) {
      case 'error': return 'bg-red-500';
      case 'completed': return 'bg-emerald-500';
      case 'paused': return 'bg-amber-500';
      default: return 'bg-gradient-to-r from-cyan-500 to-blue-500';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Загрузки</h2>
        <button
          onClick={fetchTasks}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
          title="Обновить"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading && tasks.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" />
          Загрузка списка...
        </div>
      )}

      {!loading && tasks.length === 0 && (
        <div className="text-center py-12 text-slate-400 bg-slate-800/30 rounded-2xl border border-slate-700/30">
          <Download className="w-8 h-8 mx-auto mb-3 text-slate-500" />
          Нет активных загрузок
        </div>
      )}

      <div className="space-y-3">
        {tasks.map((task) => (
          <div
            key={task.task_id}
            className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 space-y-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {statusIcon(task.status)}
                  <span className={`text-sm font-medium ${statusColor(task.status)}`}>
                    {statusText(task.status)}
                  </span>
                  <span className="text-slate-500 text-xs">
                    {task.progress.toFixed(1)}%
                  </span>
                </div>
                <p className="text-sm font-medium truncate" title={task.title || task.url}>
                  {task.title || task.url}
                </p>
                <p className="text-slate-500 text-xs truncate">{task.url}</p>
              </div>
              <div className="flex items-center gap-1">
                {/* Pause button */}
                {(task.status === 'downloading' || task.status === 'pending') && (
                  <button
                    onClick={() => pauseTask(task.task_id)}
                    className="p-2 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 transition-colors"
                    title="Поставить на паузу"
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                )}
                {/* Resume button */}
                {task.status === 'paused' && (
                  <button
                    onClick={() => resumeTask(task.task_id)}
                    className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 transition-colors"
                    title="Продолжить"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                )}
                {/* Restart button */}
                {task.status === 'error' && (
                  <button
                    onClick={() => restartTask(task.task_id)}
                    className="p-2 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
                    title="Повторить загрузку"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                )}
                {/* Download file button */}
                {task.status === 'completed' && task.filename && (
                  <button
                    onClick={() => downloadFile(task.task_id, task.filename!)}
                    className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                    title="Скачать файл"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => deleteTask(task.task_id)}
                  className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                  title="Удалить"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-700/50 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${progressColor(task.status)}`}
                style={{ width: `${Math.min(task.progress, 100)}%` }}
              />
            </div>

            {task.error_message && (
              <p className="text-red-400 text-xs bg-red-500/10 rounded-lg px-3 py-2">
                {task.error_message}
              </p>
            )}

            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>ID: {task.task_id.slice(0, 8)}</span>
              <span>{new Date(task.created_at).toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
