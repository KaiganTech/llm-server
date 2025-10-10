"""
Celery任务定义
"""
import json
import os
import sys
from datetime import datetime
from celery import current_app

# 添加项目路径
sys.path.append('/mnt/projects/llm-server')

from src.agents.kagent import KAgent
from src.diary_system.extract import extract_activity, extract_event, extract_profile
from src.diary_system.knote import DiarySystem

# 全局变量
current_day_note_path = '/mnt/projects/llm-server/src/diary_system/current_day_history.json'
agent = KAgent()
diary = DiarySystem()

@current_app.task(name='src.tasks.process_chat_task')
def process_chat_task(message, conversation_history):
    """
    处理聊天任务的异步任务
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
            'timestamp': datetime.now().isoformat()
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