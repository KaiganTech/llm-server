import json
import os
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pydantic import BaseModel

import sys
sys.path.append('/mnt/projects/llm-server')
from src.agents.kagent import KAgent
from src.diary_system.extract import extract_activity, extract_event, extract_profile
from src.diary_system.knote import DiarySystem
from celery_config import celery_app
from src.tasks import process_chat_task, organize_knotes_task

current_day_note_path = '/mnt/projects/llm-server/src/diary_system/current_day_history.json'
app = FastAPI()
agent = KAgent()
diary = DiarySystem()

# 长期记忆系统(knote)的整理函数（异步版本）
def organize_knotes():
    """触发异步整理长期记忆任务"""
    print(f"{datetime.now()}: 触发异步整理长期记忆任务...")
    # 使用Celery异步任务
    task = organize_knotes_task.delay()
    return task.id

# 定时任务设置
scheduler = BackgroundScheduler()
scheduler.add_job(organize_knotes, 'cron', hour=12)
scheduler.start()

class user_question_format(BaseModel):
    message: str

# 异步问答端点
@app.post("/ask")
async def user_question(input: user_question_format):
    """异步处理用户问题"""
    print("输入：", input.message)
    
    # 检查文件是否存在，不存在则创建
    if not os.path.exists(current_day_note_path):
        with open(current_day_note_path, 'w', encoding='utf-8') as f:
            json.dump({'conversation_history': []}, f, ensure_ascii=False, indent=4)
    
    # 检查文件是否为空
    if os.path.getsize(current_day_note_path) == 0:
        with open(current_day_note_path, 'w', encoding='utf-8') as f:
            json.dump({'conversation_history': []}, f, ensure_ascii=False, indent=4)

    # 读取对话历史
    with open(current_day_note_path, 'r', encoding='utf-8') as f:
        conversation_history = json.load(f)['conversation_history']

    # 异步调用Celery任务
    task = process_chat_task.delay(input.message, conversation_history)
    
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "任务已提交，正在异步处理中"
    }

# 任务状态查询端点
@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        response = {
            'task_id': task_id,
            'state': task_result.state,
            'status': '任务正在等待处理'
        }
    elif task_result.state == 'SUCCESS':
        response = {
            'task_id': task_id,
            'state': task_result.state,
            'status': '任务已完成',
            'result': task_result.result
        }
    else:  # FAILURE或其他状态
        response = {
            'task_id': task_id,
            'state': task_result.state,
            'status': '任务处理中或失败',
            'result': str(task_result.info) if task_result.info else None
        }
    
    return response

# 同步问答端点（兼容旧版本）
@app.post("/ask/sync")
def user_question_sync(input: user_question_format):
    """同步处理用户问题（兼容模式）"""
    print("同步处理输入：", input.message)
    
    # 检查文件是否存在，不存在则创建
    if not os.path.exists(current_day_note_path):
        with open(current_day_note_path, 'w', encoding='utf-8') as f:
            json.dump({'conversation_history': []}, f, ensure_ascii=False, indent=4)
    
    # 检查文件是否为空
    if os.path.getsize(current_day_note_path) == 0:
        with open(current_day_note_path, 'w', encoding='utf-8') as f:
            json.dump({'conversation_history': []}, f, ensure_ascii=False, indent=4)

    with open(current_day_note_path, 'r+', encoding='utf-8') as f:
        conversation_history = json.load(f)['conversation_history']
        
        agent = KAgent()
        answer = agent.chat(input.message, conversation_history)
        
        f.seek(0)
        json.dump({'conversation_history': conversation_history}, f, ensure_ascii=False, indent=4)
        f.truncate()
    
    return {"answer": answer}  

# 故障恢复机制
@app.on_event("startup")
def recovery():
    # ... existing recovery logic ...
    print("系统启动，检查并恢复中断点...")