"""
异步接口完整耗时测试脚本
测试 /ask 接口从请求提交到获取最终结果的完整耗时
"""
import requests
import json
import time 

def test_async_api_complete_timing():
    """测试异步API完整耗时（从请求到结果）"""
    
    # 测试消息
    test_message = "你能做些什么"
    
    print(f"开始测试异步接口: {test_message}")
    print("=" * 60)
    
    # 记录总开始时间
    total_start_time = time.time()
    
    # 1. 提交异步任务
    submit_start_time = time.time()
    response = requests.post(
        "http://localhost:10001/ask",
        json={"message": test_message},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    submit_end_time = time.time()
    
    if response.status_code != 200:
        print(f"请求失败: {response.status_code}")
        return
    
    # 解析响应
    result = response.json()
    task_id = result.get("task_id")
    
    if not task_id:
        print("未获取到任务ID")
        print(f"响应: {result}")
        return
    
    print(f"✅ 任务提交成功")
    print(f"   任务ID: {task_id}")
    print(f"   提交耗时: {(submit_end_time - submit_start_time):.3f}s")
    
    # 2. 轮询任务状态直到完成
    print("\n🔄 开始轮询任务状态...")
    
    poll_count = 0
    max_poll_count = 100  # 最大轮询次数
    poll_interval = 0.5     # 轮询间隔(秒)
    
    while poll_count < max_poll_count:
        poll_count += 1
        
        # 查询任务状态
        poll_start_time = time.time()
        status_response = requests.get(f"http://localhost:10001/task/{task_id}")
        poll_end_time = time.time()
        
        if status_response.status_code != 200:
            print(f"第{poll_count}次轮询失败: {status_response.status_code}")
            time.sleep(poll_interval)
            continue
        
        status_data = status_response.json()
        task_state = status_data.get("state")
        
        print(f"   第{poll_count}次轮询 - 状态: {task_state}, 查询耗时: {(poll_end_time - poll_start_time):.3f}s")
        
        # 检查任务状态
        if task_state == "SUCCESS":
            total_end_time = time.time()
            
            # 计算各种耗时
            submit_time = submit_end_time - submit_start_time
            polling_time = total_end_time - submit_end_time
            total_time = total_end_time - total_start_time
            
            print("\n" + "=" * 60)
            print("🎉 任务完成！")
            print(f"   任务结果: {status_data.get('result', 'N/A')}")
            print(f"\n📊 耗时统计:")
            print(f"   任务提交耗时: {submit_time:.3f}s")
            print(f"   任务轮询耗时: {polling_time:.3f}s")
            print(f"   总耗时: {total_time:.3f}s")
            print(f"   轮询次数: {poll_count}")
            print(f"   平均轮询间隔: {polling_time/poll_count:.3f}s")
            
            return {
                "task_id": task_id,
                "total_time": total_time,
                "submit_time": submit_time,
                "polling_time": polling_time,
                "poll_count": poll_count,
                "result": status_data.get("result")
            }
            
        elif task_state == "FAILURE":
            print(f"❌ 任务失败: {status_data}")
            return None
            
        # 等待下一次轮询
        time.sleep(poll_interval)
    
    print(f"❌ 轮询超时，超过最大轮询次数 {max_poll_count}")
    return None

def test_stream_task_progress():
    """测试流式任务的实时进度跟踪"""
    
    test_message = "你能做些什么"
    
    # 提交流式任务
    response = requests.post(
        "http://localhost:10001/ask/stream",
        json={"message": test_message},
        headers={"Content-Type": "application/json"}
    )
    task_id = response.json().get("task_id")
    
    print(f"流式任务ID: {task_id}")
    
    # 实时监控进度
    while True:
        status_response = requests.get(f"http://localhost:10001/task/{task_id}")
        status_data = status_response.json()
        print(status_data)
        # 获取流式输出数据
        result = status_data.get('result', None)
        # 显示进度信息
        print(f"轮询 - 状态: {status_data['state']}")
        if result == None:
            continue
        # 结束条件
        if status_data['state'] == 'SUCCESS':
            print("\n✅ 任务完成")
            final_result = status_data.get('result', '')
            if isinstance(final_result, dict):
                answer = final_result.get('answer', '')
                # yield answer
                for char in answer:
                    print(char, end='', flush=True)
                    time.sleep(0.05)
                print()
            break
        elif status_data['state'] == 'STREAMING':
            print("\n🔄 任务流式中")
            current_text = result.get('current_text', '')
            # yield current_text
            for char in current_text:
                print(char, end='', flush=True)
                time.sleep(0.05)
        elif status_data['state'] == 'FAILURE':
            print("❌ 任务失败:", status_data)
            break
        
        time.sleep(0.3)
    
def test_multiple_async_requests():

    """测试多个异步请求的耗时"""
    
    test_messages = [
        "你好，介绍一下你自己",
        "今天的天气怎么样",
        "Python编程有什么特点",
        "机器学习的基本概念是什么"
    ]
    
    results = []
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}/{len(test_messages)}: {message}")
        print('='*60)
        
        result = test_async_api_complete_timing()
        if result:
            results.append(result)
        
        # 测试间隔
        if i < len(test_messages):
            print(f"\n等待5秒后进行下一个测试...")
            time.sleep(5)
    
    # 统计结果
    if results:
        print("\n" + "="*60)
        print("📈 测试结果统计:")
        print("="*60)
        
        total_times = [r["total_time"] for r in results]
        submit_times = [r["submit_time"] for r in results]
        polling_times = [r["polling_time"] for r in results]
        
        print(f"测试数量: {len(results)}")
        print(f"总耗时统计:")
        print(f"  平均: {sum(total_times)/len(total_times):.3f}s")
        print(f"  最小: {min(total_times):.3f}s")
        print(f"  最大: {max(total_times):.3f}s")
        
        print(f"\n提交耗时统计:")
        print(f"  平均: {sum(submit_times)/len(submit_times):.3f}s")
        print(f"  最小: {min(submit_times):.3f}s")
        print(f"  最大: {max(submit_times):.3f}s")
        
        print(f"\n轮询耗时统计:")
        print(f"  平均: {sum(polling_times)/len(polling_times):.3f}s")
        print(f"  最小: {min(polling_times):.3f}s")
        print(f"  最大: {max(polling_times):.3f}s")

if __name__ == "__main__":
    ## 测试单个异步请求
    # print("开始测试异步接口完整耗时...")
    # test_async_api_complete_timing()

    # # 测试流式任务进度跟踪
    # print("\n开始测试流式任务进度跟踪...")
    # test_stream_task_progress()

    # # 可选：测试多个请求
    # print("\n" + "="*60)len(current_text)
    # print("开始测试多个异步请求...")
    # test_multiple_async_requests()


    test_message = "你能做些什么"
    
    # 提交流式任务
    response = requests.post(
        "http://localhost:10001/ask/stream",
        json={"message": test_message},
        headers={"Content-Type": "application/json"}
    )
    task_id = response.json().get("task_id")
    
    print(f"流式任务ID: {task_id}")

    time.sleep(3)
    status_response = requests.get(f"http://localhost:10001/task/{task_id}")
    status_data = status_response.json()
    print(status_data)
    # 获取流式输出数据
    result = status_data.get('result', None)
    print(result)