#!/bin/bash

echo "🛑 Stopping Enterprise AI Platform..."

for service in redis worker api ui ngrok; do
    if [ -f .pids/$service.pid ]; then
        PID=$(cat .pids/$service.pid)
        if ps -p $PID > /dev/null; then
            echo "Stopping $service (PID: $PID)..."
            kill $PID
        else
            echo "$service is not running."
        fi
        rm .pids/$service.pid
    else
        echo "No PID file found for $service."
    fi
done

# Catch-all for stray ngrok processes
pkill ngrok

echo "✅ All services stopped."