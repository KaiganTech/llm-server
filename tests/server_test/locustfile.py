# locustfile.py
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_history, StatsCSVFileWriter
import time
import json
import logging
import gevent
from datetime import datetime
import numpy as np
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMStressTestUser(HttpUser):
    """
    LLM服务压力测试用户
    """
    wait_time = between(0.1, 0.3)  # 基础等待时间
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_id = f"user_{id(self)}"
        self.test_prompts = self._load_test_prompts()
        
    def _load_test_prompts(self):
        """加载测试用的提示词"""
        return [
            "解释机器学习的基本概念和主要算法",
            "写一个Python函数实现快速排序算法",
            "描述Transformer架构在NLP中的应用",
            "如何评估机器学习模型的性能？",
            "比较监督学习和无监督学习的区别",
            "解释神经网络中的反向传播算法",
            "什么是注意力机制？它在深度学习中的作用是什么？",
            "写一段关于人工智能未来发展的短文",
            "解释梯度消失和梯度爆炸问题及解决方案",
            "描述BERT模型的工作原理和应用场景"
        ]
    
    def on_start(self):
        """用户启动时执行"""
        logger.info(f"用户 {self.test_id} 启动测试")
    
    @task(1)
    def test_async_inference(self):
        """异步单条文本推理测试"""
        prompt = np.random.choice(self.test_prompts[:])
        self._send_prediction_request(prompt)
    
    @task(0) 
    def test_sync_inference(self):
        """同步单条文本推理测试"""
        prompt = np.random.choice(self.test_prompts[:])
        self._send_sync_prediction_request(prompt)
    
    # @task(0)
    # def test_batch_request(self):
    #     """批量请求测试"""
    #     prompts = np.random.choice(self.test_prompts, size=2, replace=False)
    #     batch_payload = {
    #         "prompts": prompts.tolist(),
    #         "max_tokens": 80,
    #         "temperature": 0.1
    #     }
        
    #     with self.client.post(
    #         "/ask",
    #         json=batch_payload,
    #         headers={"Content-Type": "application/json"},
    #         catch_response=True,
    #         timeout=60
    #     ) as response:
    #         if response.status_code == 200:
    #             response.success()
    #             logger.debug(f"批量请求成功: {len(prompts)}个提示词")
    #         else:
    #             response.failure(f"批量请求失败: {response.status_code}")
    
    def _send_prediction_request(self, prompt):
        """发送预测请求"""
        payload = {
            "message": prompt,
        }
        
        start_time = time.time()
        
        response = self.client.post(
            "/ask",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response_time = time.time() - start_time
        if response.status_code == 200:
            # 验证响应格式
            try:
                result = response.json()
                print(f"结果： {result}")
                if "response" in result or "generated_text" in result:
                    logger.info(f"请求成功 - 响应时间: {response_time:.3f}s")
                    if "task_id" in result and "status" in result:
                        logger.info(f"异步任务提交成功 - 任务ID: {result['task_id']}")
                        
                        # 等待任务完成（可选，根据测试需求决定是否等待）
                        self._wait_for_task_completion(result['task_id'])
                else:
                    logger.error("响应格式错误")
            except json.JSONDecodeError:
                logger.error("JSON解析错误")
                
        elif response.status_code == 429:
            logger.warning("达到速率限制")
        elif response.status_code == 503:
            logger.error("服务不可用")
        else:
            logger.error(f"HTTP错误: {response.status_code}")

    def _send_sync_prediction_request(self, prompt):
        """发送同步预测请求"""
        payload = {
            "message": prompt,
        }
        
        start_time = time.time()
        
        # 发送同步请求
        response = self.client.post(
            "/ask/sync",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # 同步请求可能需要更长时间
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            # 验证同步响应格式
            try:
                result = response.json()
                if "answer" in result:
                    logger.info(f"同步请求成功 - 响应时间: {response_time:.3f}s")
                else:
                    logger.error("同步响应格式错误")
            except json.JSONDecodeError:
                logger.error("JSON解析错误")
                
        elif response.status_code == 429:
            logger.warning("达到速率限制")
        elif response.status_code == 503:
            logger.error("服务不可用")
        else:
            logger.error(f"HTTP错误: {response.status_code}")
    
    def _wait_for_task_completion(self, task_id):
        """等待异步任务完成（可选功能）"""
        max_retries = 10
        retry_interval = 1  # 秒
        
        for attempt in range(max_retries):
            time.sleep(retry_interval)
            
            # 查询任务状态
            status_response = self.client.get(f"/task/{task_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                if status_data.get('state') == 'SUCCESS':
                    logger.info(f"异步任务完成 - 结果: {status_data.get('result', {})}")
                    return True
                elif status_data.get('state') == 'FAILURE':
                    logger.error(f"异步任务失败: {status_data.get('result', '未知错误')}")
                    return False
                # PENDING 或 STARTED 状态继续等待
            else:
                logger.error(f"查询任务状态失败: {status_response.status_code}")
                return False
        
        logger.warning(f"任务 {task_id} 超时")
        return False