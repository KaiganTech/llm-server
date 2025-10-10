"""
Celery任务监控
"""
import time
from celery_config import celery_app

def monitor_celery_queues():
    """监控Celery队列状态"""
    try:
        # 获取Redis连接
        redis_client = celery_app.connection().channel().client
        
        # 获取队列长度
        chat_queue_len = redis_client.llen('celery')
        background_queue_len = redis_client.llen('celery')
        
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 队列监控:")
        print(f"  聊天队列长度: {chat_queue_len}")
        print(f"  后台队列长度: {background_queue_len}")
        
        # 获取活跃worker数量
        i = celery_app.control.inspect()
        active_workers = i.active()
        if active_workers:
            worker_count = len(active_workers)
            print(f"  活跃Worker数量: {worker_count}")
        else:
            print("  没有活跃的Worker")
            
    except Exception as e:
        print(f"监控错误: {e}")

if __name__ == "__main__":
    while True:
        monitor_celery_queues()
        time.sleep(30)  # 每30秒监控一次