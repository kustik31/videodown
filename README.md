# VideoDown

Универсальное приложение для скачивания видео с YouTube и сотен других платформ с помощью yt-dlp.


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

### Локальный запуск (без Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Backend: `http://localhost:8000`

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Frontend: `http://localhost:5173`

**Скрипт для запуска обоих:**
- Windows: `start.bat`
- Linux/Mac: `start.sh`

### Docker (рекомендуется)

```bash
# Запуск всего приложения
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

### Сборка production

```bash
cd frontend
npm run build
```

Статические файлы будут в `frontend/dist/`

## API Endpoints

- `GET /health` — проверка работоспособности
- `GET /` — информация об API
- `POST /api/info` — получить информацию о видео
- `POST /api/download` — начать загрузку
- `GET /api/download/{task_id}` — статус загрузки
- `GET /api/downloads` — список всех загрузок
- `GET /api/download/{task_id}/file` — скачать файл
- `DELETE /api/download/{task_id}` — удалить загрузку

## CI/CD

В репозитории настроен GitHub Actions workflow (`.github/workflows/ci.yml`) для автоматической сборки frontend при каждом push в `main`.

## Деплой

### Cloudflare Pages (frontend only)
1. Соберите frontend: `npm run build`
2. Загрузите содержимое `frontend/dist/` на Cloudflare Pages

### Docker Compose (полный стек)
```bash
docker-compose up -d
```

## Структура проекта

```
videodown/
├── backend/
│   ├── main.py              # FastAPI приложение
│   ├── download_service.py  # Сервис загрузки (yt-dlp)
│   ├── requirements.txt     # Python зависимости
│   └── Dockerfile           # Docker образ backend
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Главный компонент
│   │   ├── components/
│   │   │   ├── VideoDownloader.tsx  # Панель загрузки
│   │   │   └── DownloadList.tsx     # Список загрузок
│   │   └── index.css        # Стили Tailwind
│   ├── Dockerfile           # Docker образ frontend (nginx)
│   ├── nginx.conf           # Конфиг nginx
│   └── package.json         # Node.js зависимости
├── docker-compose.yml       # Docker Compose конфиг
├── .github/workflows/ci.yml # GitHub Actions CI
├── start.bat                # Скрипт запуска (Windows)
├── start.sh                 # Скрипт запуска (Linux/Mac)
└── README.md                # Этот файл
```

## Лицензия

MIT License. Используйте ответственно.
