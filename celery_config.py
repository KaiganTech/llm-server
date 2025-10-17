"""
Celery配置
"""
import os
import sys
from celery import Celery

# 添加项目路径到Python路径
project_root = '/mnt/projects/llm-server'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 创建Celery应用
celery_app = Celery('llm_server')

# 配置Celery
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',  # Redis作为消息代理
    result_backend='redis://localhost:6379/0',  # Redis作为结果后端
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_routes={
        'src.tasks.process_chat_stream_task': {'queue': 'chat_queue'},
        'src.tasks.organize_knotes_task': {'queue': 'background_queue'},
    },
    task_default_queue='default',
    task_default_exchange='llm_server',
    task_default_routing_key='default',
    worker_prefetch_multiplier=100,  # 控制并发度
    worker_max_tasks_per_child=500,  # 防止内存泄漏
    task_acks_late=False,  # 任务完成后无需确认
    worker_disable_rate_limits=True,  # 禁用速率限制以提高性能
    task_time_limit=60,  # 任务超时时间（秒）
    task_soft_time_limit=50,  # 软超时时间（秒）
    broker_connection_retry_on_startup=True,  # 启动时重试连接
    task_ignore_result=False,  # 保留结果用于状态查询
    task_store_errors_even_if_ignored=True,  # 存储错误信息
    worker_send_task_events=True,  # 启用任务事件
    task_send_sent_event=True,  # 发送任务事件
    worker_direct=True # 直接发送任务给空闲Worker
)

# 自动发现任务
celery_app.autodiscover_tasks(['src.tasks'], force=True)