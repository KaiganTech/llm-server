#!/bin/bash

# vLLM服务监控脚本

LOG_DIR="/mnt/projects/llm-server/logs/vllm_serve"
PID_FILE="$LOG_DIR/vllm_service.pid"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查服务状态
check_status() {
    if [ -f "$PID_FILE" ]; then
        VLLM_PID=$(cat "$PID_FILE")
        if ps -p $VLLM_PID > /dev/null; then
            echo -e "${GREEN}✓ vLLM服务正在运行 (PID: $VLLM_PID)${NC}"
            return 0
        else
            echo -e "${RED}✗ vLLM服务进程不存在${NC}"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo -e "${RED}✗ vLLM服务未运行${NC}"
        return 1
    fi
}

# 检查API连通性
check_api() {
    echo -e "${BLUE}测试API连通性...${NC}"
    RESPONSE=$(curl -s -w "\\n%{http_code}" "http://localhost:8080/v1/models" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    CONTENT=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ API连通性正常${NC}"
        echo "模型信息:"
        echo "$CONTENT" | python -m json.tool 2>/dev/null || echo "$CONTENT"
    else
        echo -e "${RED}✗ API连通性异常 (HTTP $HTTP_CODE)${NC}"
    fi
}

# 检查GPU使用情况
check_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        echo -e "${BLUE}GPU使用情况:${NC}"
        nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader
    else
        echo -e "${YELLOW}⚠ nvidia-smi不可用${NC}"
    fi
}

# 检查内存使用
check_memory() {
    echo -e "${BLUE}系统内存使用:${NC}"
    free -h
}

# 检查日志文件大小
check_logs() {
    echo -e "${BLUE}日志文件状态:${NC}"
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            size=$(du -h "$log_file" | cut -f1)
            lines=$(wc -l < "$log_file")
            echo "  $(basename "$log_file"): $size, $lines 行"
        fi
    done
}

# 实时监控
realtime_monitor() {
    echo -e "${BLUE}开始实时监控 (Ctrl+C 退出)...${NC}"
    while true; do
        clear
        echo "=== vLLM服务实时监控 ==="
        echo "时间: $(date)"
        echo ""
        
        check_status
        if [ $? -eq 0 ]; then
            check_api
            echo ""
            check_gpu
            echo ""
            check_memory
            echo ""
            check_logs
        fi
        
        sleep 10
    done
}

# 主函数
main() {
    case "$1" in
        "status")
            check_status
            if [ $? -eq 0 ]; then
                check_api
            fi
            ;;
        "api")
            check_api
            ;;
        "gpu")
            check_gpu
            ;;
        "memory")
            check_memory
            ;;
        "logs")
            check_logs
            ;;
        "realtime")
            realtime_monitor
            ;;
        "all")
            check_status
            if [ $? -eq 0 ]; then
                check_api
                echo ""
                check_gpu
                echo ""
                check_memory
                echo ""
                check_logs
            fi
            ;;
        *)
            echo "用法: $0 {status|api|gpu|memory|logs|realtime|all}"
            echo "  status    - 检查服务状态"
            echo "  api       - 测试API连通性"
            echo "  gpu       - 检查GPU使用情况"
            echo "  memory    - 检查内存使用"
            echo "  logs      - 检查日志文件"
            echo "  realtime  - 实时监控"
            echo "  all       - 完整检查"
            ;;
    esac
}

main "$@"