
"""
性能测试脚本 - 测试/ask/stream与/task接口的最大可接收数据频率
"""
import requests
import time

messages_dict = ["你好，介绍一下你自己",
        "今天的天气怎么样",
        "Python编程有什么特点",
        "机器学习的基本概念是什么",
        "你能做些什么"]

class StreamPerformanceTester:
    def __init__(self, base_url="http://localhost:10001"):
        self.base_url = base_url
        self.results = []
        
    def send_stream_request(self, request_id):
        """发送流式请求并监控完整处理时间 - 调用script_test.py中的函数"""
        # 保存原始测试消息
        original_test_message = messages_dict[request_id % len(messages_dict)]
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 使用script_test.py中的test_stream_task_progress函数
            # 由于原函数没有返回值，我们需要重写一个版本
            test_message = original_test_message
            
            # 提交流式任务
            response = requests.post(
                f"{self.base_url}/ask/stream",
                json={"message": test_message},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return None
                
            task_data = response.json()
            task_id = task_data.get("task_id")
            
            if not task_id:
                return None
            
            # 轮询任务状态直到完成
            poll_count = 0
            max_polls = 300  # 最大轮询次数（5分钟超时）
            
            while poll_count < max_polls:
                poll_count += 1
                
                # 查询任务状态
                status_response = requests.get(f"{self.base_url}/task/{task_id}")
                if status_response.status_code != 200:
                    continue
                    
                status_data = status_response.json()
                task_state = status_data.get("state")
                
                if task_state == "SUCCESS":
                    end_time = time.time()
                    total_time = end_time - start_time
                    
                    return {
                        "request_id": request_id,
                        "task_id": task_id,
                        "total_time": total_time,
                        "poll_count": poll_count,
                        "success": True
                    }
                elif task_state == "FAILURE":
                    return {
                        "request_id": request_id,
                        "task_id": task_id,
                        "total_time": time.time() - start_time,
                        "poll_count": poll_count,
                        "success": False,
                        "error": "Task failed"
                    }
                
                # 等待下一次轮询
                time.sleep(0.01)
            
            # 超时
            return {
                "request_id": request_id,
                "task_id": task_id,
                "total_time": time.time() - start_time,
                "poll_count": poll_count,
                "success": False,
                "error": "Timeout"
            }
            
        except Exception as e:
            return {
                "request_id": request_id,
                "total_time": 0,
                "success": False,
                "error": str(e)
            }
    
    def test_fixed_rate(self, requests_per_second=10, duration_seconds=30):
        """测试固定频率下的性能 - 修复版：并行发送请求"""
        print(f"\n🎯 开始固定频率测试: {requests_per_second}Hz, 持续时间: {duration_seconds}秒")
        print("=" * 70)
        
        total_requests = requests_per_second * duration_seconds
        interval = 1.0 / requests_per_second  # 发送间隔（秒）
        
        # 使用线程池并行发送请求
        import concurrent.futures
        import threading
        
        results = []
        results_lock = threading.Lock()
        request_counter = 0
        
        def send_request_wrapper(request_id):
            """包装发送请求函数"""
            try:
                result = self.send_stream_request(request_id)
                with results_lock:
                    results.append(result)
                    
                    if result and result.get("success"):
                        print(f"✅ 请求 {request_id}: 成功, 耗时 {result['total_time']:.2f}s")
                    elif result:
                        print(f"❌ 请求 {request_id}: 失败 - {result.get('error', 'Unknown error')}")
                    else:
                        print(f"❌ 请求 {request_id}: 无响应")
                        
            except Exception as e:
                print(f"❌ 请求 {request_id}: 异常 - {e}")
        
        start_time = time.time()
        
        # 使用线程池管理并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(50, requests_per_second * 2)) as executor:
            futures = []
            
            # 按固定频率发送请求
            while request_counter < total_requests:
                current_time = time.time()
                elapsed = current_time - start_time
                
                if elapsed >= duration_seconds:
                    break
                
                # 提交请求到线程池
                future = executor.submit(send_request_wrapper, request_counter)
                futures.append(future)
                
                request_counter += 1
                
                # 控制发送速率
                next_send_time = start_time + (request_counter * interval)
                sleep_time = next_send_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # 等待所有请求提交完成
            print(f"📤 已提交 {len(futures)} 个请求，等待完成...")
        
        # 等待所有请求完成（最长等待时间 = 测试时长 + 最大处理时间）
        max_wait_time = duration_seconds + 60  # 额外60秒等待处理完成
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time:
            completed = sum(1 for f in futures if f.done())
            total = len(futures)
            
            if completed == total:
                break
                
            print(f"⏳ 等待请求完成: {completed}/{total} (已等待 {time.time() - wait_start:.1f}s)")
            time.sleep(2)
        
        # 统计结果
        self._analyze_results(results, requests_per_second, duration_seconds)
        return results
    
    def test_max_capacity(self, max_requests_per_second=50, step_size=5, test_duration=20):
        """测试最大可接收数据频率"""
        print(f"\n🚀 开始最大容量测试 (最大频率: {max_requests_per_second}Hz, 步长: {step_size}Hz)")
        print("=" * 70)
        
        capacity_results = []
        
        for rate in range(step_size, max_requests_per_second + 1, step_size):
            print(f"\n📊 测试频率: {rate}Hz")
            print("-" * 40)
            
            results = self.test_fixed_rate(rate, test_duration)
            
            # 计算成功率
            successful_requests = [r for r in results if r.get("success", False)]
            success_rate = len(successful_requests) / len(results) * 100 if results else 0
            
            # 计算平均响应时间
            if successful_requests:
                avg_response_time = sum(r["total_time"] for r in successful_requests) / len(successful_requests)
            else:
                avg_response_time = 0
            
            capacity_result = {
                "rate_hz": rate,
                "total_requests": len(results),
                "successful_requests": len(successful_requests),
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "results": results
            }
            
            capacity_results.append(capacity_result)
            
            print(f"📈 频率 {rate}Hz 结果:")
            print(f"   成功率: {success_rate:.1f}%")
            print(f"   平均响应时间: {avg_response_time:.2f}s")
            
            # 如果成功率低于90%，认为达到极限
            if success_rate < 90:
                print(f"⚠️  频率 {rate}Hz 已达到系统极限")
                break
            
            # 等待系统恢复
            print("等待5秒让系统恢复...")
            time.sleep(5)
        
        # 输出最大容量分析
        self._print_capacity_analysis(capacity_results)
        return capacity_results
    
    def _analyze_results(self, results, target_rate, duration):
        """分析测试结果"""
        if not results:
            print("❌ 没有测试结果")
            return
        
        # 过滤掉None值，防止AttributeError
        valid_results = [r for r in results if r is not None]
        if len(valid_results) < len(results):
            print(f"⚠️  发现 {len(results) - len(valid_results)} 个无效结果(None)，已过滤")
        
        successful_requests = [r for r in valid_results if r.get("success", False)]
        failed_requests = [r for r in valid_results if not r.get("success", False)]
        
        success_rate = len(successful_requests) / len(results) * 100
        
        if successful_requests:
            response_times = [r["total_time"] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        print("\n" + "=" * 70)
        print("📊 性能测试结果统计:")
        print("=" * 70)
        print(f"目标频率: {target_rate}Hz")
        print(f"测试时长: {duration}秒")
        print(f"总请求数: {len(results)}")
        print(f"成功请求: {len(successful_requests)}")
        print(f"失败请求: {len(failed_requests)}")
        print(f"成功率: {success_rate:.1f}%")
        
        if successful_requests:
            print(f"平均响应时间: {avg_response_time:.2f}s")
            print(f"最大响应时间: {max_response_time:.2f}s")
            print(f"最小响应时间: {min_response_time:.2f}s")
        
        # 吞吐量分析
        actual_rate = len(successful_requests) / duration
        target_rate = len(results) / duration  # 实际发送频率
        
        print(f"目标发送频率: {target_rate:.1f} requests/second")
        print(f"实际完成频率: {actual_rate:.1f} requests/second")
        print(f"系统处理能力: {actual_rate/target_rate*100:.1f}% (相对于发送频率)")
        
        # 计算系统最大并发处理能力
        if successful_requests:
            avg_processing_time = sum(r["total_time"] for r in successful_requests) / len(successful_requests)
            max_concurrent_capacity = 1 / avg_processing_time if avg_processing_time > 0 else 0
            print(f"系统理论最大并发处理能力: {max_concurrent_capacity:.1f} requests/second")
        
        if success_rate >= 95:
            print("✅ 系统性能良好")
        elif success_rate >= 80:
            print("⚠️  系统性能一般，建议优化")
        else:
            print("❌ 系统性能较差，需要优化")
    
    def _print_capacity_analysis(self, capacity_results):
        """输出最大容量分析"""
        print("\n" + "=" * 70)
        print("🚀 最大容量测试结果分析")
        print("=" * 70)
        
        if not capacity_results:
            print("❌ 没有容量测试结果")
            return
        
        # 找到最大稳定频率
        max_stable_rate = 0
        for result in capacity_results:
            if result["success_rate"] >= 95:
                max_stable_rate = result["rate_hz"]
        
        print(f"📈 最大稳定频率: {max_stable_rate}Hz")
        
        # 找到系统极限频率
        system_limit = 0
        for result in capacity_results:
            if result["success_rate"] >= 80:
                system_limit = result["rate_hz"]
        
        print(f"⚠️  系统极限频率: {system_limit}Hz")
        
        # 推荐配置
        recommended_rate = max_stable_rate * 0.8  # 80%的安全余量
        print(f"💡 推荐生产频率: {recommended_rate:.1f}Hz")
        
        # 详细结果表格
        print("\n详细结果:")
        print("频率(Hz) | 成功率(%) | 平均响应时间(s)")
        print("-" * 40)
        for result in capacity_results:
            print(f"{result['rate_hz']:7} | {result['success_rate']:8.1f} | {result['avg_response_time']:15.2f}")

def main():
    """主函数"""
    tester = StreamPerformanceTester()
    
    print("🎯 流式接口性能测试工具")
    print("=" * 50)
    print("1. 固定频率测试")
    print("2. 最大容量测试")
    print("3. 自定义测试")
    
    choice = input("请选择测试模式 (1-3): ").strip()
    
    if choice == "1":
        # 固定频率测试
        rate = int(input("请输入测试频率 (Hz): ") or "10")
        duration = int(input("请输入测试时长 (秒): ") or "30")
        tester.test_fixed_rate(rate, duration)
        
    elif choice == "2":
        # 最大容量测试
        max_rate = int(input("请输入最大测试频率 (Hz): ") or "50")
        step = int(input("请输入步长 (Hz): ") or "5")
        duration = int(input("请输入每个频率的测试时长 (秒): ") or "20")
        tester.test_max_capacity(max_rate, step, duration)
        
    elif choice == "3":
        # 自定义测试
        print("\n自定义测试选项:")
        print("1. 测试单个请求的完整流程")
        print("2. 测试特定频率范围")
        
        sub_choice = input("请选择: ").strip()
        
        if sub_choice == "1":
            # 测试单个请求
            result = tester.send_stream_request(0)
            if result:
                print(f"单个请求结果: {result}")
        elif sub_choice == "2":
            # 测试特定频率范围
            start_rate = int(input("起始频率 (Hz): ") or "5")
            end_rate = int(input("结束频率 (Hz): ") or "30")
            step = int(input("步长 (Hz): ") or "5")
            duration = int(input("测试时长 (秒): ") or "15")
            
            for rate in range(start_rate, end_rate + 1, step):
                print(f"\n测试频率: {rate}Hz")
                tester.test_fixed_rate(rate, duration)
                time.sleep(3)  # 间隔休息
    
    else:
        print("无效选择，使用默认配置进行最大容量测试")
        tester.test_max_capacity()


if __name__ == "__main__":
    main()