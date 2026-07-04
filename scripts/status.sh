#!/bin/bash

echo "📊 System Status:"
echo "-----------------"

check_status() {
    if [ -f .pids/$1.pid ] && ps -p $(cat .pids/$1.pid) > /dev/null; then
        echo "✓ $2 is running"
    else
        echo "✗ $2 is OFFLINE"
    fi
}

check_status "redis" "Redis Server"
check_status "worker" "RQ Worker"
check_status "api" "FastAPI Server"
check_status "ui" "Streamlit UI"
check_status "ngrok" "Ngrok Tunnel"
echo "-----------------"