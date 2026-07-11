#!/bin/bash
set -e

# Start backend in background
cd backend
pip install -r requirements.txt
python main.py &
BACKEND_PID=$!

# Start frontend
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "Applications started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both"

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
echo
wait
