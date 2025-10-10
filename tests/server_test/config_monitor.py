# config_monitor.py
import psutil
import time
import threading
import pandas as pd
from datetime import datetime
from locustfile import logger

class SystemMonitor:
    """系统资源监控"""
    
    def __init__(self, interval=2.0):
        self.interval = interval
        self.monitoring = False
        self.metrics = []
        
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("🔍 开始系统资源监控")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 停止系统资源监控")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics.append(metrics)
            except Exception as e:
                logger.error(f"监控数据收集失败: {e}")
            
            time.sleep(self.interval)
    
    def _collect_metrics(self):
        """收集系统指标"""
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        
        # 获取Python进程资源使用
        process = psutil.Process()
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'timestamp': datetime.now(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / 1024 / 1024,
            'process_memory_mb': process_memory,
            'disk_read_mb': disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
            'disk_write_mb': disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
            'bytes_sent_mb': net_io.bytes_sent / 1024 / 1024,
            'bytes_recv_mb': net_io.bytes_recv / 1024 / 1024
        }
    
    def save_metrics(self, filename="system_metrics.csv"):
        """保存监控数据"""
        if self.metrics:
            df = pd.DataFrame(self.metrics)
            df.to_csv(filename, index=False)
            logger.info(f"💾 系统监控数据保存至: {filename}")

# 全局测试配置
TEST_CONFIG = {
    "host": "http://localhost:10001",
    "test_scenarios": [
        {
            "name": "baseline",
            "users": 10,
            "spawn_rate": 5,
            "duration": "2m"
        },
        {
            "name": "medium_load", 
            "users": 50,
            "spawn_rate": 10,
            "duration": "3m"
        },
        {
            "name": "high_load",
            "users": 100,
            "spawn_rate": 20,
            "duration": "5m"
        },
        {
            "name": "stress_test",
            "users": 200,
            "spawn_rate": 25,
            "duration": "5m"
        }
    ],
    "target_rps_tests": [10, 25, 50, 100, 150, 200]
}