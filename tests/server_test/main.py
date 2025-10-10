# main.py
import asyncio
import time
import json
import numpy as np
from datetime import datetime
from test_runner import LocustTestRunner
from config_monitor import SystemMonitor, TEST_CONFIG

def main():
    """主测试程序"""
    print("🚀 FastAPI大模型服务最大频率测试")
    print("=" * 50)
    
    # 初始化
    runner = LocustTestRunner(TEST_CONFIG["host"])
    monitor = SystemMonitor()
    
    try:
        # 开始系统监控
        monitor.start_monitoring()
        
        # 1. 基准测试
        print("\n1. 运行基准测试...")
        runner.run_stress_test(target_rps=10, duration="2m")
        time.sleep(10)  # 冷却时间
        
        # 2. 阶梯负载测试
        print("\n2. 运行阶梯负载测试...")
        runner.run_step_load_test(steps=[(20, "1m"), (50, "2m"), (100, "3m")])
        time.sleep(10)
        
        # 3. 目标RPS测试
        print("\n3. 运行目标RPS测试...")
        for target_rps in TEST_CONFIG["target_rps_tests"]:
            print(f"\n--> 测试目标RPS: {target_rps}")
            runner.run_stress_test(target_rps=target_rps, duration="3m")
            time.sleep(15)  # 测试间冷却
        
        # 4. 最大负载测试
        print("\n4. 运行最大负载测试...")
        runner.run_frequency_sweep_test(
            max_users=200,
            spawn_rate=25,
            run_time="10m"
        )
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试执行错误: {e}")
    finally:
        # 停止监控并保存数据
        monitor.stop_monitoring()
        monitor.save_metrics()
        
        # 生成测试报告
        generate_test_report(runner, monitor)
        
        print(f"\n✅ 测试完成! 结果文件:")
        print("   - frequency_sweep.csv")
        print("   - system_metrics.csv") 
        print("   - 各种HTML报告文件")

def generate_test_report(runner, monitor):
    """生成测试报告"""
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "test_config": TEST_CONFIG,
        "system_metrics_summary": {
            "max_cpu_usage": max([m['cpu_percent'] for m in monitor.metrics]) if monitor.metrics else 0,
            "max_memory_usage": max([m['memory_percent'] for m in monitor.metrics]) if monitor.metrics else 0,
            "avg_cpu_usage": np.mean([m['cpu_percent'] for m in monitor.metrics]) if monitor.metrics else 0,
        },
        "performance_results": runner.results
    }
    
    with open("test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()