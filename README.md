# VideoDown

Универсальное приложение для скачивания видео с YouTube и сотен других платформ с помощью yt-dlp.

## ⚠️ Важное предупреждение

Это приложение предназначено только для загрузки видео, которые вы имеете право скачивать. Пожалуйста, уважайте авторские права и условия использования соответствующих платформ.

**КиноПоиск не поддерживается напрямую**, так как использует DRM-защиту контента.

## Поддерживаемые платформы

- YouTube
- Vimeo
- TikTok
- Instagram
- Twitter/X
- Facebook
- VK
- Rutube
- И сотни других (через yt-dlp)

## Архитектура

- **Backend**: Python + FastAPI + yt-dlp
- **Frontend**: React + TypeScript + Vite + Tailwind CSS

## Установка и запуск

### Требования

- Python 3.9+
- Node.js 18+
- FFmpeg (опционально, для лучшей совместимости)

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend будет доступен на `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен на `http://localhost:5173`

### Сборка production

```bash
cd frontend
npm run build
```

Статические файлы будут в `frontend/dist/`

## API Endpoints

- `POST /api/info` — получить информацию о видео
- `POST /api/download` — начать загрузку
- `GET /api/download/{task_id}` — статус загрузки
- `GET /api/downloads` — список всех загрузок
- `GET /api/download/{task_id}/file` — скачать файл
- `DELETE /api/download/{task_id}` — удалить загрузку

## GitHub + Cloudflare

Для деплоя на Cloudflare Pages:
1. Соберите frontend: `npm run build`
2. Загрузите содержимое `frontend/dist/` на Cloudflare Pages
3. Для backend можно использовать Cloudflare Workers с Python (экспериментально) или другой хостинг

## Лицензия

MIT License. Используйте ответственно.
