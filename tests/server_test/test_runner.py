# test_runner.py
import subprocess
import threading
from datetime import datetime
from locustfile import logger

class LocustTestRunner:
    """Locust测试运行器"""
    
    def __init__(self, host="http://localhost:8000"):
        self.host = host
        self.results = []
        self.current_test = None
        
    def run_frequency_sweep_test(self, max_users=100, spawn_rate=10, 
                               run_time="5m", step_duration=60):
        """
        运行频率扫描测试
        """
        logger.info("🚀 开始频率扫描压力测试")
        
        # 启动Locust主进程
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", self.host,
            "--users", str(max_users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", run_time,
            "--headless",
            "--csv", "frequency_sweep",
            "--html", "frequency_sweep_report.html",
            "--loglevel", "INFO",
            "--print-stats"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # 实时输出日志
            for line in process.stdout:
                print(line.strip())
                if "RPS" in line:  # 提取RPS信息
                    self._parse_rps_line(line)
            
            process.wait()
            logger.info("✅ 频率扫描测试完成")
            
        except Exception as e:
            logger.error(f"❌ 测试执行失败: {e}")
    
    def run_step_load_test(self, steps=[(10, "1m"), (50, "2m"), (100, "3m")]):
        """
        阶梯式负载测试
        """
        logger.info("📈 开始阶梯式负载测试")
        
        step_configs = []
        for users, duration in steps:
            step_configs.append(f"{users}:{duration}")
        
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", self.host,
            "--headless",
            "--step-load",
            "--step-users", ",".join([str(step[0]) for step in steps]),
            "--step-time", ",".join([step[1] for step in steps]),
            "--csv", "step_load",
            "--html", "step_load_report.html"
        ]
        
        self._run_locust_command(cmd, "阶梯式负载")
    
    def run_stress_test(self, target_rps, duration="10m"):
        """
        目标RPS压力测试
        """
        logger.info(f"🎯 开始目标RPS测试: {target_rps} RPS, 持续时间: {duration}")
        
        # 计算需要的用户数 (经验公式)
        estimated_users = max(10, int(target_rps * 2))
        
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", self.host,
            "--users", str(estimated_users),
            "--spawn-rate", str(min(estimated_users, 50)),
            "--run-time", duration,
            "--headless",
            "--csv", f"stress_test_{target_rps}rps",
            "--html", f"stress_test_{target_rps}rps_report.html"
        ]
        
        self._run_locust_command(cmd, f"目标RPS测试({target_rps})")
    
    def _run_locust_command(self, cmd, test_name):
        """执行Locust命令"""
        try:
            self.current_test = test_name
            start_time = datetime.now()
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if process.returncode == 0:
                logger.info(f"✅ {test_name} 完成, 耗时: {duration:.1f}s")
            else:
                logger.error(f"❌ {test_name} 失败: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {test_name} 超时")
        except Exception as e:
            logger.error(f"❌ {test_name} 异常: {e}")
    
    def _parse_rps_line(self, line):
        """解析RPS输出行"""
        try:
            # 解析类似: "Requests/sec: 125.35" 的输出
            if "Requests/sec:" in line:
                parts = line.split()
                rps = float(parts[parts.index("Requests/sec:") + 1])
                self.results.append({
                    'timestamp': datetime.now(),
                    'rps': rps,
                    'test': self.current_test
                })
        except:
            pass