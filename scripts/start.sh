#!/bin/bash

# Ensure directories exist
mkdir -p logs .pids

echo "🚀 Starting Enterprise AI Platform..."

# 1. Start Redis
if ! pgrep -x "redis-server" > /dev/null
then
    echo "Starting Redis..."
    nohup redis-server > logs/redis.log 2>&1 &
    echo $! > .pids/redis.pid
else
    echo "Redis is already running."
fi

# 2. Start RQ Worker (with Apple fork safety override)
echo "Starting RQ Worker..."
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
nohup rq worker enterprise_tasks > logs/worker.log 2>&1 &
echo $! > .pids/worker.pid

# 3. Start FastAPI
echo "Starting FastAPI..."
nohup uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload > logs/api.log 2>&1 &
echo $! > .pids/api.pid

# 4. Start Streamlit (assuming your UI is in app_ui.py)
echo "Starting Streamlit UI..."
nohup uv run streamlit run app_ui.py --server.port 8501 > logs/ui.log 2>&1 &
echo $! > .pids/ui.pid

# 5. Start Ngrok
echo "Starting Ngrok tunnel on port 8000..."
nohup ngrok http 8000 > logs/ngrok.log 2>&1 &
echo $! > .pids/ngrok.pid

echo "✅ All services started successfully!"
echo "API Docs: http://localhost:8000/docs"
echo "UI:       http://localhost:8501"
echo "Run 'make status' to verify."