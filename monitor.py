"""
Celery任务监控
"""
import time
from celery_config import celery_app

def monitor_celery_queues():
    """监控Celery队列状态"""
    try:
        # 获取Redis连接
        with celery_app.connection() as conn:
            redis_client = conn.channel().client
            
            # 获取所有队列长度（包括默认队列）
            chat_queue_len = redis_client.llen('celery')  # Celery默认队列前缀
            background_queue_len = redis_client.llen('celery')  # 同上
            
            # 尝试获取特定队列
            try:
                chat_queue_len = redis_client.llen('chat_queue')
                background_queue_len = redis_client.llen('background_queue')
                default_queue_len = redis_client.llen('default')
            except:
                # 如果特定队列不存在，使用默认队列
                chat_queue_len = redis_client.llen('celery')
                background_queue_len = redis_client.llen('celery')
                default_queue_len = redis_client.llen('celery')
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 队列监控:")
            print(f"  聊天队列长度: {chat_queue_len}")
            print(f"  后台队列长度: {background_queue_len}")
            print(f"  默认队列长度: {default_queue_len}")
            
            # 获取活跃worker数量
            i = celery_app.control.inspect()
            active_workers = i.active()
            if active_workers:
                worker_count = len(active_workers)
                print(f"  活跃Worker数量: {worker_count}")
                
                # 显示每个worker的详细信息
                for worker_name, tasks in active_workers.items():
                    print(f"    Worker {worker_name}: {len(tasks)} 个活跃任务")
            else:
                print("  没有活跃的Worker")
                
    except Exception as e:
        print(f"监控错误: {e}")

if __name__ == "__main__":
    while True:
        monitor_celery_queues()
        time.sleep(1)  # 每1秒监控一次