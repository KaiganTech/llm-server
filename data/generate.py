# 调用大模型模拟生成社交陪伴多轮对话数据集

import json
import os
from datetime import datetime

import sys
sys.path.append('/home/kai/robot')
from src.utils.kllm import call_api

# system_prompt1 = """你扮演有心理障碍的用户，你需要和其他用户进行社交交流，分享自己的经历和情感。"""
# system_prompt2 = """你扮演一名能够和有心理障碍的用户进行社交陪伴的助手，你需通过语言去陪伴用户。"""
system_prompt1 = """你扮演一名用户，你需要进行社交交流，可以提出自己的问题，也可以分享自己的经历与情感。不要提及你的问题类型"""
system_prompt2 = """你扮演一名社交陪伴助手，你需通过语言去与用户交流，去陪伴用户。不要提及你是什么角色/助手"""

# 对话配置
DIALOGUE_ROUNDS = 10  # 每轮对话回合数
DIALOGUE_SESSIONS = 1  # 生成多少组对话
OUTPUT_DIR = "/home/kai/robot/data/dialogues"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_dialogue():
    """生成一组完整的对话"""
    dialogue = []
    
    # 初始化角色
    user_state = {"emotion": "积极", "topic": "生活社交"}
    assistant_state = {"approach": "gentle"}
    
    # 首轮用户发言
    user_prompt = f"当前情感状态：{user_state['emotion']}\n想讨论的话题：{user_state['topic']}"
    user_msg = call_api(system_prompt=system_prompt1, user_prompt=user_prompt, temperature=0.8, max_tokens=32768, model_name="Qwen2.5-72B-Instruct-GGUF")
    dialogue.append({"role": "user", "content": user_msg})
    
    # 多轮对话
    for _ in range(DIALOGUE_ROUNDS):
        # 助手回复
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in dialogue[-3:]])
        assistant_prompt = f"对话上下文：\n{context}"
        assistant_msg = call_api(system_prompt=system_prompt2, user_prompt=assistant_prompt, temperature=0.8, max_tokens=32768, model_name="Qwen2.5-72B-Instruct-GGUF")
        dialogue.append({"role": "assistant", "content": assistant_msg})
        
        # 用户回应
        user_response_prompt = f"助手最后回复：{assistant_msg}"
        user_msg = call_api(system_prompt=system_prompt1, user_prompt=user_response_prompt, temperature=0.8, max_tokens=32768, model_name="Qwen2.5-72B-Instruct-GGUF")
        dialogue.append({"role": "user", "content": user_msg})
    
    return dialogue

def save_dialogue(session_id, dialogue):
    """保存对话数据并提取QA对"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dialogue_{session_id}_{timestamp}.json"
    
    # 保存完整对话和QA数据
    data = {
        "metadata": {
            "session_id": session_id,
            "timestamp": timestamp,
            "user_state": {"emotion": "anxious", "topic": "work pressure"}
        },
        "dialogue": dialogue,
    }
    
    with open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    for session in range(DIALOGUE_SESSIONS):
        print(f"正在生成第{session+1}组对话...")
        dialogue = generate_dialogue()
        save_dialogue(session+1, dialogue)
    print(f"所有对话已生成，保存在：{OUTPUT_DIR}")

