#!/bin/bash

# vLLM优化启动脚本
# 增加并发数量和性能优化配置

# 设置环境变量
export VLLM_LOGGING_CONFIG_PATH="/mnt/projects/llm-server/vllm/logs.json"
export VLLM_LOGGING_LEVEL="INFO"
export VLLM_WORKER_MULTIPROC_METHOD="spawn"  # 避免fork内存问题

# 模型配置
MODEL_PATH="/mnt/models/qwen3-4b-instruct-2507-fp8"
HOST="0.0.0.0"
PORT="8080"

# 性能优化配置
GPU_MEMORY_UTILIZATION="0.8"
TENSOR_PARALLEL_SIZE="2"
MAX_NUM_SEQS="256"           # 减少最大并发序列数以优化长上下文
MAX_MODEL_LEN="16384"        # 减少最大模型长度以提升性能
BLOCK_SIZE="16"              # KV缓存块大小
ENABLE_PREFIX_CACHING="true" # 启用前缀缓存
SWAP_SPACE="16"              # 交换空间大小(GB)

# 并发优化配置
MAX_PARALLEL_LOADING_WORKERS="4" # 并行加载工作线程数
MAX_NUM_BATCHED_TOKENS="4096"    # 批处理最大token数

# 日志目录
LOG_DIR="/mnt/projects/llm-server/logs/vllm_serve"
mkdir -p "$LOG_DIR"

echo "启动优化版vLLM服务..."
echo "模型: $MODEL_PATH"
echo "地址: $HOST:$PORT"
echo "GPU内存利用率: $GPU_MEMORY_UTILIZATION"
echo "张量并行: $TENSOR_PARALLEL_SIZE"
echo "最大并发序列: $MAX_NUM_SEQS"
echo "日志配置: $VLLM_LOGGING_CONFIG_PATH"

# 检查端口占用
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "错误: 端口 $PORT 已被占用"
    exit 1
fi

# 启动vLLM服务（使用优化配置）
vllm serve "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
    --max-num-seqs "$MAX_NUM_SEQS" \
    --max-model-len "$MAX_MODEL_LEN" \
    --block-size "$BLOCK_SIZE" \
    --enable-prefix-caching \
    --swap-space "$SWAP_SPACE" \
    --max-parallel-loading-workers "$MAX_PARALLEL_LOADING_WORKERS" \
    --max-num-batched-tokens "$MAX_NUM_BATCHED_TOKENS" \
    --served-model-name "qwen3-4b-instruct-2507-fp8" \
    
VLLM_PID=$!
echo "vLLM服务PID: $VLLM_PID"

# 保存PID
echo "$VLLM_PID" > "$LOG_DIR/vllm_service.pid"

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 检查服务状态
if ps -p $VLLM_PID > /dev/null; then
    echo "vLLM服务启动成功!"
    
    # 测试服务连通性
    echo "测试服务连通性..."
    if curl -s "http://$HOST:$PORT/v1/models" > /dev/null 2>&1; then
        echo "✓ 服务连通性正常"
    else
        echo "⚠ 服务连通性测试失败，但进程仍在运行"
    fi
    
    echo ""
    echo "服务信息:"
    echo "  API地址: http://$HOST:$PORT/v1"
    echo "  模型端点: http://$HOST:$PORT/v1/models"
    echo "  聊天端点: http://$HOST:$PORT/v1/chat/completions"
    echo "  日志文件: $LOG_DIR/"
    echo ""
    echo "日志文件说明:"
    echo "  vllm_service.log - 服务运行日志"
    echo "  vllm_errors.log  - 错误日志"
    echo "  vllm_access.log   - 访问日志"
    echo "  vllm_performance.log - 性能日志"
    echo ""
    echo "查看实时日志: tail -f $LOG_DIR/vllm_service.log"
else
    echo "错误: vLLM服务启动失败"
    echo "请检查日志文件: $LOG_DIR/vllm_service.log"
    exit 1
fi