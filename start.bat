@echo off
REM Start backend
cd backend
start cmd /k "pip install -r requirements.txt && python main.py"
REM Start frontend
cd ..\frontend
start cmd /k "npm install && npm run dev"
echo Applications started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
