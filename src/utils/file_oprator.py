import os
import json
import fcntl

def safe_file_operation(operation_type, file_path, data=None):
    """
    线程安全的文件操作函数
    
    Args:
        operation_type: 'read' 或 'write'
        file_path: 文件路径
        data: 写入的数据（仅write操作需要）
    
    Returns:
        read操作返回读取的数据，write操作返回None
    """
    if operation_type == 'read':
        # 检查文件是否存在，不存在则创建
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump({'conversation_history': []}, f, ensure_ascii=False, indent=4)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        # 检查文件是否为空
        if os.path.getsize(file_path) == 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump({'conversation_history': []}, f, ensure_ascii=False, indent=4)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # 共享锁用于读取
            try:
                content = json.load(f)
                return content.get('conversation_history', [])
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    elif operation_type == 'write':
        if data is None:
            raise ValueError("写入操作需要提供data参数")
        
        # 写入文件内容
        with open(file_path, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 排他锁用于写入
            try:
                json.dump({'conversation_history': data}, f, ensure_ascii=False, indent=4)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    else:
        raise ValueError("不支持的operation_type，必须是'read'或'write'")