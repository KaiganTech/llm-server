#!/bin/bash

# 启动Celery Worker
echo "启动Celery Worker..."

# 启动聊天队列worker
celery -A celery_config worker --loglevel=info --queues=chat_queue --concurrency=4 --hostname=worker1@%h &

# 启动后台任务队列worker  
celery -A celery_config worker --loglevel=info --queues=background_queue --concurrency=2 --hostname=worker2@%h &

# 启动默认队列worker
celery -A celery_config worker --loglevel=info --queues=default --concurrency=2 --hostname=worker3@%h &

echo "Celery Workers 启动完成"
echo "使用 'ps aux | grep celery' 查看进程状态"
echo "使用 'pkill -f celery' 停止所有worker"