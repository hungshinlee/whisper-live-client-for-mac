#!/bin/bash
# 清理佔用 port 9090 的程序

PORT=9090

PID=$(lsof -ti:$PORT)

if [ -z "$PID" ]; then
    echo "Port $PORT 沒有被佔用"
else
    echo "正在終止佔用 port $PORT 的程序 (PID: $PID)..."
    kill -9 $PID
    echo "已清理完成"
fi
