# 思维链 + 非JSON格式化输出
from typing import Dict, Any, List, Generator, Union
import json
import time

import sys
sys.path.append('/mnt/projects/llm-server')
from src.utils.kllm import call_api, call_api_stream

# 初始化LLM配置
temperature = 0.01
max_tokens = 32768
model_name = "qwen3-4b-instruct-2507-fp8"

class KAgent:
    """
    使用思维链(Chain of Thought)的Agent
    将情绪分析整合到思维链中，减少API调用次数
    """
    
    def __init__(self):
        # 整合情绪分析的思维链提示词
        self.cod_prompt = """
## 角色
你是一个贴心的社交陪伴助手，需要按照思维链步骤处理用户输入。

## 思维链处理步骤

### 步骤1: 情绪识别与分析
分析用户当前的情绪状态，包括：
- 主要情绪：[喜悦、信任、恐惧、惊讶、悲伤、厌恶、愤怒、期待]
- 情绪效价(valence): 积极情绪接近 +1, 消极情绪接近 -1, 中性为 0
- 情绪唤醒度(arousal): 高能量情绪接近 1, 低能量情绪接近 0

### 步骤2: 意图识别与分类
识别用户的真实意图和需求：
- greeting: 问候/打招呼
- question: 提问/咨询
- sharing_feelings: 分享感受
- seeking_comfort: 寻求安慰
- small_talk: 闲聊
- goodbye: 告别
- other: 其他

### 步骤3: 情境理解与上下文分析
结合对话历史理解当前情境：
- 用户情绪变化趋势
- 对话主题连贯性
- 用户潜在需求

### 步骤4: 响应策略制定
基于以上分析制定回应策略：
- **寻求安慰**: 表达理解、提供情感支持、给予积极建议
- **告别**: 友好结束对话、表达祝福、邀请再次交流  
- **分享感受**: 认真倾听、表达共情、适当分享类似经历
- **问题咨询**: 提供准确信息、保持专业但温暖的态度
- **问候**: 热情回应、开启话题

## 输出格式
请基于以上分析直接输出最终回应内容，要自然、温暖、人性化，不要包含任何JSON格式或其他额外信息。
"""
    
    def _build_conversation_context(self, user_input: str, conversation_history: List[Dict]) -> str:
        """构建对话上下文"""
        if not conversation_history:
            return f"当前用户输入: {user_input}\n历史对话: 无"
        
        # 只保留最近对话以减少token消耗
        recent_history = conversation_history[:]  # XX全轮次的对话
        history_str = "\n".join([
            f"{msg['role']}: {msg['content']}" + 
            (f" [情绪: {msg.get('emotion', '未知')}]" if msg.get('emotion') else "")
            for msg in recent_history
        ])
        
        return f"""当前用户输入: {user_input}
历史对话:
{history_str}"""
   
    def chat(self, user_input: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """非流式聊天接口"""

        if conversation_history is None:
            conversation_history = []

        # 构建完整的提示词
        context = self._build_conversation_context(user_input, conversation_history)
        
        user_prompt = f"""
## 对话上下文
{context}

## 处理要求
请严格按照思维链步骤分析以上对话，确保情绪分析和意图识别准确。
最终回应要自然、温暖、人性化，展现同理心。

请直接输出最终回应内容，不要包含任何JSON格式或其他额外信息。
"""
        
        try:
            # 使用流式API调用，只获取最终回应
            cod_time_start = time.time()
            response = call_api(
                system_prompt=self.cod_prompt,
                user_prompt=user_prompt,
                temperature=0.1,  # 较低温度保证情绪分析准确性
                max_tokens=5000,  # 增加token以容纳情绪分析
                model_name=model_name
            )
            cod_time_end = time.time()
            cod_time_consume = cod_time_end - cod_time_start
            
            print(f"\n====思维链流式输出完成==== 耗时: {cod_time_consume:.3f}s")
            return response
            
        except Exception as e:
            print(f"思维链处理失败: {e}")
            return "思维链处理失败"
    
    def chat_stream(self, user_input: str, conversation_history: List[Dict] = None) -> Generator[str, None, None]:
        """流式聊天接口"""
        if conversation_history is None:
            conversation_history = []
            
        # 构建对话上下文
        context = self._build_conversation_context(user_input, conversation_history)
        
        user_prompt = f"""
## 对话上下文
{context}

## 处理要求
请严格按照思维链步骤分析以上对话，确保情绪分析和意图识别准确。
最终回应要自然、温暖、人性化，展现同理心。

请直接输出最终回应内容，不要包含任何JSON格式或其他额外信息。
"""
        
        try:
            # 使用流式API调用
            cod_time_start = time.time()
            
            # 流式调用API
            for chunk in call_api_stream(
                system_prompt=self.cod_prompt,
                user_prompt=user_prompt,
                temperature=0.1,  # 较低温度保证情绪分析准确性
                max_tokens=5000,  # 增加token以容纳情绪分析
                model_name=model_name
            ):
                if chunk:
                    yield chunk
            
            cod_time_end = time.time()
            cod_time_consume = cod_time_end - cod_time_start
            
            print(f"\n====思维链流式输出完成==== 耗时: {cod_time_consume:.3f}s")
            
        except Exception as e:
            print(f"思维链流式处理失败: {e}")
            yield "思维链流式处理失败"

def main():
    agent = KAgent()
    
    # 测试对话 - 涵盖不同情绪和意图
    test_cases_1 = [
        {
            "input": "你好，我今天感觉特别开心，刚刚得到了升职的机会！",
            "description": "积极情绪-分享好消息"
        },
        {
            "input": "工作压力好大，每天加班到很晚，感觉快要崩溃了...",
            "description": "消极情绪-寻求安慰"  
        },
        {
            "input": "我最近总是担心未来的发展，不知道该怎么办",
            "description": "焦虑情绪-寻求建议"
        },
        {
            "input": "今天的天气真好啊，阳光明媚的",
            "description": "中性情绪-闲聊"
        },
        {
            "input": "再见，谢谢你的陪伴",
            "description": "告别意图"
        }
    ]

    test_cases = [
        {
            "input": "你好，我今天感觉特别开心，刚刚得到了升职的机会！",
            "description": "积极情绪-分享好消息"
        },
    ]

    print("=== 整合情绪分析的思维链测试 ===\n")
    conversation_history = []
    total_start_time = time.time()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试案例 {i}: {test_case['description']}")
        print(f"{'='*50}")
        
        print(f"用户: {test_case['input']}")
        
        # 获取详细分析报告
        result = agent.chat(test_case['input'], conversation_history)
        
        print(f"\n助手: {result}")
        print("\n" + "*-" * 25)
    
    total_time = time.time() - total_start_time
    print(f"\n=== 测试总结 ===")
    print(f"总对话轮数: {len(test_cases)}")
    print(f"总耗时: {total_time:.3f}s")
    print(f"平均每轮: {total_time/len(test_cases):.3f}s")

def main_stream():
    agent = KAgent()
    
    # 测试对话 - 涵盖不同情绪和意图
    test_cases_1 = [
        {
            "input": "你好，我今天感觉特别开心，刚刚得到了升职的机会！",
            "description": "积极情绪-分享好消息"
        },
        {
            "input": "工作压力好大，每天加班到很晚，感觉快要崩溃了...",
            "description": "消极情绪-寻求安慰"  
        },
        {
            "input": "我最近总是担心未来的发展，不知道该怎么办",
            "description": "焦虑情绪-寻求建议"
        },
        {
            "input": "今天的天气真好啊，阳光明媚的",
            "description": "中性情绪-闲聊"
        },
        {
            "input": "再见，谢谢你的陪伴",
            "description": "告别意图"
        }
    ]

    test_cases = [
        {
            "input": "你好，我今天感觉特别开心，刚刚得到了升职的机会！",
            "description": "积极情绪-分享好消息"
        },
    ]

    print("=== 整合情绪分析的思维链测试 ===\n")
    conversation_history = []
    total_start_time = time.time()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试案例 {i}: {test_case['description']}")
        print(f"{'='*50}")
        
        print(f"用户: {test_case['input']}")
        
        # 获取详细分析报告
        start_time = time.time()
        first_chunk = True
        for chunk in agent.chat_stream(test_case['input'], conversation_history):
            if first_chunk and chunk:
                first_char_time = time.time() - start_time
                print(f"\n首字符出现耗时: {first_char_time:.3f}s")
                first_chunk = False
            print(chunk, end='', flush=True)
        print("\n" + "*-" * 25)
    
    total_time = time.time() - total_start_time
    print(f"\n=== 测试总结 ===")
    print(f"总对话轮数: {len(test_cases)}")
    print(f"总耗时: {total_time:.3f}s")
    print(f"平均每轮: {total_time/len(test_cases):.3f}s")

if __name__ == "__main__":
    # main()
    main_stream()