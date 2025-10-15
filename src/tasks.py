"""
Celery任务定义
"""
import json
import os
import sys
from datetime import datetime
from celery import current_app
from celery.result import AsyncResult

# 添加项目路径
sys.path.append('/mnt/projects/llm-server')

from src.agents.kagentv1 import KAgent
from src.diary_system.extract import extract_activity, extract_event, extract_profile
from src.diary_system.knote import DiarySystem

# 全局变量
current_day_note_path = '/mnt/projects/llm-server/src/diary_system/current_day_history.json'
agent = KAgent()
diary = DiarySystem()

@current_app.task(name='src.tasks.process_chat_task')
def process_chat_task(message, conversation_history):
    """
    处理聊天任务的异步任务(非流式)
    """
    try:
        print(f"[{datetime.now()}] 处理聊天任务: {message[:50]}...")
        
        # 调用KAgent进行聊天处理
        answer = agent.chat(message, conversation_history)
        # 保存到文件
        save_conversation_history(conversation_history)
        
        return {
            'status': 'success',
            'answer': answer,
            'timestamp': datetime.now().isoformat(),
            'stream_processed': False
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@current_app.task(name='src.tasks.process_chat_stream_task')
def process_chat_stream_task(message, conversation_history):
    """
    处理聊天任务的异步任务(流式)
    """
    try:
        print(f"[{datetime.now()}] 处理流式聊天任务: {message[:50]}...")
        task_id = process_chat_stream_task.request.id
        # 使用Celery结果后端存储流式输出
        current_app.backend.store_result(
            task_id,
            {
                'current_text': '',
                'chunks': [],
                'last_update': datetime.now().isoformat(),
                'status': 'streaming'
            },
            'STREAMING'
        )

        # 调用KAgent进行流式聊天处理
        stream_response = agent.chat_stream(message, conversation_history)
        # 收集所有流式响应片段并实时更新
        answer_chunks = []
        for chunk in stream_response:
            if chunk:
                answer_chunks.append(chunk)
                # 实时更新流式输出到结果后端
                current_app.backend.store_result(
                    task_id,
                    {
                        'current_text': ''.join(answer_chunks),
                        'chunks': answer_chunks.copy(),
                        'last_update': datetime.now().isoformat(),
                        'status': 'streaming'
                    },
                    'STREAMING'
                )
        
        # 合并所有片段
        full_answer = ''.join(answer_chunks)
        
        # 保存到文件
        save_conversation_history(conversation_history)

        return {
            'status': 'success',
            'answer': full_answer,
            'timestamp': datetime.now().isoformat(),
            'stream_processed': True
        }
    except Exception as e:

        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@current_app.task(name='src.tasks.organize_knotes_task')
def organize_knotes_task():
    """
    整理长期记忆的异步任务
    """
    try:
        print(f"[{datetime.now()}] 开始整理长期记忆...")
        
        # 检查文件是否存在
        if not os.path.exists(current_day_note_path):
            return {'status': 'error', 'error': '对话历史文件不存在'}
        
        # 读取对话历史
        with open(current_day_note_path, 'r', encoding='utf-8') as f:
            conversation_history = json.load(f)['conversation_history']
        
        if not conversation_history:
            return {'status': 'success', 'message': '没有需要整理的对话历史'}
        
        # 提取信息
        user_prompt = "对话：\n" + "\n".join([f"{item['role']}: {item['content']}" for item in conversation_history])
        activity_content = extract_activity(user_prompt)
        event_content = extract_event(user_prompt)
        profile_content = extract_profile(user_prompt)
        
        # 添加到日记系统
        diary.add_entry('activity', activity_content)
        diary.add_entry('event', event_content)
        diary.add_entry('profile', profile_content)
        
        # 清空当天的对话历史
        save_conversation_history([])
        
        return {
            'status': 'success',
            'message': '长期记忆整理完成',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def save_conversation_history(conversation_history):
    """
    保存对话历史到文件
    """
    with open(current_day_note_path, 'w', encoding='utf-8') as f:
        json.dump({'conversation_history': conversation_history}, f, ensure_ascii=False, indent=4)

def get_stream_task_output(task_id: str):
    """
    获取流式任务的实时输出
    """
    try:
        # 从Celery结果后端获取流式输出
        result = AsyncResult(task_id, app=current_app)
        
        # 检查任务状态
        if result.state == 'STREAMING':
            # 获取流式输出数据
            stream_data = result.result
            if stream_data and isinstance(stream_data, dict):
                print(f"从Celery结果后端获取流式输出成功: {stream_data.get('current_text', '')}")
                return stream_data
        elif result.state == 'SUCCESS':
            # 任务已完成，返回最终结果
            final_result = result.result
            if final_result and isinstance(final_result, dict):
                print(f"任务已完成，返回最终结果")
                return {
                    'current_text': final_result.get('answer', ''),
                    'chunks': [final_result.get('answer', '')],
                    'last_update': final_result.get('timestamp', datetime.now().isoformat()),
                    'status': 'completed'
                }
        
        print(f"任务状态: {result.state}")
        return None
    except Exception as e:
        print(f"获取流式输出失败: {e}")
        return None