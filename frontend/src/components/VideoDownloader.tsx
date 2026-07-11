import { useState } from 'react';
import { Link, Download, Loader2, AlertCircle, Film, Music, Video, Globe } from 'lucide-react';

interface VideoFormat {
  format_id: string;
  ext: string;
  resolution: string | null;
  fps: number | null;
  filesize: number | null;
  vcodec: string | null;
  acodec: string | null;
}

interface VideoInfo {
  title: string;
  duration: number | null;
  thumbnail: string | null;
  uploader: string | null;
  formats: VideoFormat[];
  webpage_url: string;
  extractor: string;
}

const API_BASE = '/api';

export default function VideoDownloader() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState<VideoInfo | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<string>('');
  const [downloading, setDownloading] = useState(false);
  const [taskId, setTaskId] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [quality, setQuality] = useState('best');

  const [proxy, setProxy] = useState('');
  const [showProxy, setShowProxy] = useState(false);

  const fetchInfo = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    setInfo(null);
    try {
      const res = await fetch(`${API_BASE}/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, proxy: proxy || undefined }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to fetch info');
      }
      const data = await res.json();
      setInfo(data);
      // Default to best video+audio or first available
      const best = data.formats.find((f: VideoFormat) => 
        f.vcodec && f.vcodec !== 'none' && f.acodec && f.acodec !== 'none'
      );
      setSelectedFormat(best?.format_id || data.formats[0]?.format_id || '');
    } catch (e: any) {
      setError(e.message || 'Ошибка получения информации о видео');
    } finally {
      setLoading(false);
    }
  };

  const startDownload = async () => {
    if (!info || !selectedFormat) return;
    setDownloading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, format_id: selectedFormat, quality, proxy: proxy || undefined }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to start download');
      }
      const data = await res.json();
      setTaskId(data.task_id);
    } catch (e: any) {
      setError(e.message || 'Ошибка запуска загрузки');
      setDownloading(false);
    }
  };

  const formatSize = (bytes: number | null) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '—';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const videoFormats = info?.formats.filter(f => f.vcodec && f.vcodec !== 'none') || [];
  const audioFormats = info?.formats.filter(f => f.acodec && f.acodec !== 'none' && (!f.vcodec || f.vcodec === 'none')) || [];

  return (
    <div className="space-y-6">
      {/* URL Input */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Link className="w-5 h-5 text-cyan-400" />
          Вставьте ссылку на видео
        </h2>
        <div className="flex gap-3">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="flex-1 bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all placeholder:text-slate-500"
            onKeyDown={(e) => e.key === 'Enter' && fetchInfo()}
          />
          <button
            onClick={fetchInfo}
            disabled={loading || !url.trim()}
            className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl font-medium text-sm hover:from-cyan-400 hover:to-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Film className="w-4 h-4" />}
            {loading ? 'Анализ...' : 'Анализировать'}
          </button>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <button
            onClick={() => setShowProxy(!showProxy)}
            className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1 transition-colors"
          >
            <Globe className="w-3 h-3" />
            {showProxy ? 'Скрыть настройки прокси' : 'Настройки прокси'}
          </button>
          <span className="text-xs text-slate-500">
            {proxy ? `Прокси: ${proxy}` : 'Без прокси'}
          </span>
        </div>

        {showProxy && (
          <div className="mt-2">
            <input
              type="text"
              value={proxy}
              onChange={(e) => setProxy(e.target.value)}
              placeholder="http://user:pass@host:port  или  socks5://host:port"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all placeholder:text-slate-600"
            />
            <p className="mt-1 text-xs text-slate-500">
              Форматы: http://host:port, https://user:pass@host:port, socks5://host:port
            </p>
          </div>
        )}

        {error && (
          <div className="mt-3 flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {/* Video Info */}
      {info && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 space-y-6">
          <div className="flex gap-4">
            {info.thumbnail && (
              <img
                src={info.thumbnail}
                alt={info.title}
                className="w-40 h-24 object-cover rounded-xl border border-slate-700"
              />
            )}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg leading-tight mb-1 truncate">{info.title}</h3>
              <p className="text-slate-400 text-sm">{info.uploader || 'Unknown uploader'}</p>
              <p className="text-slate-500 text-sm mt-1">Длительность: {formatDuration(info.duration)}</p>
              <p className="text-slate-500 text-xs mt-1">Источник: {info.extractor}</p>
            </div>
          </div>

          {/* Format Selection */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-slate-300 flex items-center gap-2">
              <Video className="w-4 h-4 text-cyan-400" />
              Выберите формат видео
            </h4>
            <div className="max-h-64 overflow-y-auto space-y-1 pr-1">
              {videoFormats.length > 0 ? (
                videoFormats.map((f) => (
                  <label
                    key={f.format_id}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl border cursor-pointer transition-all ${
                      selectedFormat === f.format_id
                        ? 'bg-cyan-500/10 border-cyan-500/30'
                        : 'bg-slate-900/50 border-slate-700/50 hover:border-slate-600'
                    }`}
                  >
                    <input
                      type="radio"
                      name="format"
                      value={f.format_id}
                      checked={selectedFormat === f.format_id}
                      onChange={() => setSelectedFormat(f.format_id)}
                      className="accent-cyan-500"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">
                          {f.resolution || 'Audio only'}
                          {f.fps ? ` • ${f.fps}fps` : ''}
                          {' • '}{f.ext}
                        </span>
                        <span className="text-slate-400 text-xs">{formatSize(f.filesize)}</span>
                      </div>
                      <div className="text-slate-500 text-xs mt-0.5">
                        {f.vcodec && f.vcodec !== 'none' ? `Video: ${f.vcodec}` : ''}
                        {f.acodec && f.acodec !== 'none' ? ` • Audio: ${f.acodec}` : ''}
                      </div>
                    </div>
                  </label>
                ))
              ) : (
                <p className="text-slate-500 text-sm">Нет доступных видео-форматов</p>
              )}
            </div>
          </div>

          {/* Audio-only option */}
          {audioFormats.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-medium text-sm text-slate-300 flex items-center gap-2">
                <Music className="w-4 h-4 text-cyan-400" />
                Или аудио только
              </h4>
              <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                {audioFormats.slice(0, 10).map((f) => (
                  <label
                    key={f.format_id}
                    className={`flex items-center gap-3 px-4 py-2 rounded-xl border cursor-pointer transition-all ${
                      selectedFormat === f.format_id
                        ? 'bg-cyan-500/10 border-cyan-500/30'
                        : 'bg-slate-900/50 border-slate-700/50 hover:border-slate-600'
                    }`}
                  >
                    <input
                      type="radio"
                      name="format"
                      value={f.format_id}
                      checked={selectedFormat === f.format_id}
                      onChange={() => setSelectedFormat(f.format_id)}
                      className="accent-cyan-500"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{f.ext} • Audio</span>
                        <span className="text-slate-400 text-xs">{formatSize(f.filesize)}</span>
                      </div>
                      <div className="text-slate-500 text-xs">{f.acodec}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Download Button */}
          <button
            onClick={startDownload}
            disabled={downloading || !selectedFormat}
            className="w-full py-3 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl font-medium text-sm hover:from-emerald-400 hover:to-teal-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {downloading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Загрузка запущена (ID: {taskId.slice(0, 8)}...)
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Скачать видео
              </>
            )}
          </button>

          {downloading && taskId && (
            <p className="text-center text-sm text-cyan-400">
              Перейдите в раздел «Загрузки» для отслеживания прогресса
            </p>
          )}
        </div>
      )}
    </div>
  );
}
