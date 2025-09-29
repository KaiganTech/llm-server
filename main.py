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

current_day_note_path = '/mnt/projects/llm-server/src/diary_system/current_day_history.json'
app = FastAPI()
agent = KAgent()
diary = DiarySystem()

# 长期记忆系统(knote)的整理函数
def organize_knotes():
    # ... existing knote system code ...
    print(f"{datetime.now()}: 正在整理长期记忆（写日记中）...写完日记当天的短期记忆清空")
    with open(current_day_note_path, 'r', encoding='utf-8') as f:
        conversation_history = json.load(f)['conversation_history']
        user_prompt = "对话：\n" + "\n".join([f"{item['role']}: {item['content']}" for item in conversation_history])
        activity_content = extract_activity(user_prompt)
        event_content = extract_event(user_prompt)
        profile_content = extract_profile(user_prompt)

# 定时任务设置
scheduler = BackgroundScheduler()
scheduler.add_job(organize_knotes, 'cron', hour=0)
scheduler.start()

class user_question_format(BaseModel):
    message: str

# 实时问答端点
@app.post("/ask")
def user_question(input: user_question_format):
    print("输入：", input.message)
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
        answer = agent.chat(input.message, conversation_history)
        f.seek(0)
        json.dump({'conversation_history': conversation_history}, f, ensure_ascii=False, indent=4)
        f.truncate()
    return  {"answer": answer}  

# 故障恢复机制
@app.on_event("startup")
def recovery():
    # ... existing recovery logic ...
    print("系统启动，检查并恢复中断点...")