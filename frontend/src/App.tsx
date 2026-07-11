import { useState, useEffect } from 'react';
import VideoDownloader from './components/VideoDownloader';
import DownloadList from './components/DownloadList';
import { Download, List, Info } from 'lucide-react';

export type View = 'download' | 'list' | 'about';

function App() {
  const [view, setView] = useState<View>('download');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <nav className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Download className="w-6 h-6 text-cyan-400" />
            <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              VideoDown
            </h1>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => setView('download')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                view === 'download'
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Download className="w-4 h-4" />
              Скачать
            </button>
            <button
              onClick={() => setView('list')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                view === 'list'
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <List className="w-4 h-4" />
              Загрузки
            </button>
            <button
              onClick={() => setView('about')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                view === 'about'
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Info className="w-4 h-4" />
              О проекте
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {view === 'download' && <VideoDownloader />}
        {view === 'list' && <DownloadList />}
        {view === 'about' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8">
              <h2 className="text-2xl font-bold mb-4">О VideoDown</h2>
              <p className="text-slate-300 mb-4">
                VideoDown — это универсальное приложение для скачивания видео с различных платформ.
                Оно использует мощный движок yt-dlp для поддержки сотен видеохостингов.
              </p>
              <h3 className="text-lg font-semibold mb-2 text-cyan-400">Поддерживаемые платформы</h3>
              <ul className="list-disc list-inside text-slate-300 space-y-1 mb-4">
                <li>YouTube</li>
                <li>Vimeo</li>
                <li>TikTok</li>
                <li>Instagram</li>
                <li>Twitter/X</li>
                <li>Facebook</li>
                <li>VK</li>
                <li>Rutube</li>
                <li>И сотни других...</li>
              </ul>
              <h3 className="text-lg font-semibold mb-2 text-cyan-400">Важно</h3>
              <p className="text-slate-300 mb-4">
                Это приложение предназначено только для загрузки видео, которые вы имеете право скачивать.
                Пожалуйста, уважайте авторские права и условия использования соответствующих платформ.
              </p>
              <p className="text-slate-400 text-sm">
                КиноПоиск не поддерживается напрямую, так как использует DRM-защиту контента.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
