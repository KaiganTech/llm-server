# Celery异步任务系统设置指南

## 系统架构

- **FastAPI**: 主Web框架，提供API接口
- **Celery**: 分布式任务队列，处理异步任务
- **Redis**: 消息代理和结果后端
- **多个Worker**: 不同队列的专用worker

## 安装和启动

### 0. 模型准备
```bash
VLLM_LOGGING_CONFIG_PATH=/mnt/projects/llm-server/logs/vllm_serve/logs.json vllm serve qwen3-4b-instruct-2507-fp8 --host 0.0.0.0 --port 8080 --gpu-memory-utilization 0.8 --tensor-parallel-size 2
```

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动Redis服务
```bash
# 使用Docker Compose
docker-compose up -d

# 或者直接运行Redis
redis-server
```

### 3. 启动Celery Workers
```bash
# 方式1: 使用启动脚本
chmod +x start_celery_worker.sh
./start_celery_worker.sh

# 方式2: 手动启动
celery -A celery_config worker --loglevel=info --queues=chat_queue --concurrency=4
celery -A celery_config worker --loglevel=info --queues=background_queue --concurrency=2
```

### 4. 启动FastAPI服务
```bash
uvicorn main:app --host 0.0.0.0 --port 10001 --reload
```

## API接口

### 异步问答接口
- **POST** `/ask` - 提交异步聊天任务
- **GET** `/task/{task_id}` - 查询任务状态

### 同步问答接口（兼容）
- **POST** `/ask/sync` - 同步处理聊天（兼容旧版本）

## 性能优化

### 队列配置
- `chat_queue`: 聊天任务队列，并发度4
- `background_queue`: 后台任务队列，并发度2  
- `default`: 默认队列，并发度2

### 监控
```bash
# 启动监控
python src/monitor.py

# 查看Celery状态
celery -A celery_config status
```
## 故障排除

1. **Redis连接失败**: 检查Redis服务是否运行
2. **Worker无法启动**: 检查依赖是否安装完整
3. **任务积压**: 增加worker并发度或优化任务处理