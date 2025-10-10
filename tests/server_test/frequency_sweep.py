# frequency_sweep.py
import time 
import gevent
from locustfile import logger

class FrequencySweepUser(HttpUser):
    """
    频率扫描测试 - 逐步增加请求频率
    """
    fixed_count = 1  # 固定用户数，通过调整等待时间控制频率
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_frequency = 1.0  # Hz
        self.request_interval = 1.0 / self.current_frequency
        self.test_start_time = time.time()
        
    @task
    def frequency_controlled_request(self):
        """频率控制的请求"""
        prompt = "测试大模型服务性能和处理能力"
        payload = {
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        with self.client.post(
            "/predict",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            timeout=10
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")
        
        # 根据当前频率计算等待时间
        gevent.sleep(self.request_interval)
    
    def update_frequency(self, new_frequency):
        """动态更新请求频率"""
        self.current_frequency = new_frequency
        self.request_interval = 1.0 / new_frequency
        logger.info(f"更新频率: {new_frequency} Hz, 间隔: {self.request_interval:.3f}s")