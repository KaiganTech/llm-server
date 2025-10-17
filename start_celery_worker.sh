#!/bin/bash

# 启动Celery Worker
echo "启动Celery Worker..."

# 检查Redis是否运行
if ! redis-cli ping > /dev/null 2>&1; then
    echo "错误: Redis服务未运行，请先启动Redis"
    exit 1
fi

# 设置不同的日志文件
LOG_DIR="/mnt/projects/llm-server/logs"
mkdir -p "$LOG_DIR"

# 启动聊天队列worker
echo "启动聊天队列Worker..."
celery -A celery_config worker --loglevel=info --queues=chat_queue --concurrency=96 --hostname=worker1@%h --logfile="$LOG_DIR/worker1.log" &
WORKER1_PID=$!
echo "聊天队列Worker PID: $WORKER1_PID"

# 等待2秒确保第一个Worker启动
sleep 2

# 启动后台任务队列worker  
echo "启动后台任务队列Worker..."
celery -A celery_config worker --loglevel=info --queues=background_queue --concurrency=2 --hostname=worker2@%h --logfile="$LOG_DIR/worker2.log" &
WORKER2_PID=$!
echo "后台任务队列Worker PID: $WORKER2_PID"

# 等待2秒确保第二个Worker启动
sleep 2

# 启动默认队列worker
echo "启动默认队列Worker..."
celery -A celery_config worker --loglevel=info --queues=default --concurrency=2 --hostname=worker3@%h --logfile="$LOG_DIR/worker3.log" &
WORKER3_PID=$!
echo "默认队列Worker PID: $WORKER3_PID"

# 等待所有Worker启动完成
sleep 5

# 检查Worker是否成功启动
WORKER_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
echo "当前运行的Celery Worker数量: $WORKER_COUNT"

if [ "$WORKER_COUNT" -lt 3 ]; then
    echo "警告: 只有 $WORKER_COUNT 个Worker成功启动，预期3个"
    echo "检查日志文件: $LOG_DIR/worker*.log"
else
    echo "所有3个Worker成功启动"
fi

echo "Celery Workers 启动完成"
echo "使用 'ps aux | grep celery' 查看进程状态"
echo "使用 'pkill -f celery' 停止所有worker"
echo "日志文件位置: $LOG_DIR/worker*.log"