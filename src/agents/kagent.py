from typing import Dict, Any, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import json

import sys
sys.path.append('/mnt/projects/llm-server')
from src.utils.kllm import call_api

# 定义状态结构
class AgentState(TypedDict):
    messages: [List[BaseMessage]]
    user_intent: str
    user_mood: str
    conversation_history: List[Dict[str, Any]]
    needs_response: bool

# 初始化LLM
temperature=0.01
max_tokens=32768
model_name="Qwen2.5-72B-Instruct-GGUF"

class KAgent:
    def __init__(self):
        self.graph = self._build_graph()
        self._visualize_graph()
    
    def _build_graph(self):
        """构建LangGraph流程图"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("receive_input", self._receive_input)
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_special_case", self._handle_special_case)
        # 设置入口点
        workflow.set_entry_point("receive_input")
        
        # 添加边（定义流程）
        workflow.add_edge("receive_input", "analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_based_on_intent,
            {
                "normal": "generate_response",
                "special": "handle_special_case",
            }
        )
        workflow.add_edge("handle_special_case", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _visualize_graph(self):
        """可视化LangGraph流程图"""
        mermaid_code = self.graph.get_graph().draw_mermaid()
        with open("graph.mmd", "w", encoding="utf-8") as f:
            f.write(mermaid_code)
    
    def _receive_input(self, state: AgentState) -> AgentState:
        """接收用户输入"""
        print("====用户输入==== ", state["messages"])
        state["conversation_history"].append({"role": "human", "content": state["messages"][-1].content})
        return state
    
    def _analyze_intent(self, state: AgentState) -> AgentState:
        """分析用户意图和情绪"""
        last_message = state["messages"][-1]
        user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in state["conversation_history"][:-1]])
        print("====意图分析-历史数据==== ", history_str)
        # 意图分析prompt
        intent_prompt = """
        你是一个专业的情感分析和意图识别模型，能够分析用户输入的情感和意图。
        """
        user_prompt = """
        请分析以下用户输入的意图和情绪状态。返回JSON格式：
        
        {{
            "intent": "greeting|question|sharing_feelings|seeking_comfort|small_talk|goodbye|other",
            "mood": "happy|sad|anxious|neutral|excited|angry|tired",
            "urgency": "low|medium|high",
            "needs_comfort": true/false,
            "topics": ["话题1", "话题2", ...]
        }}
        
        用户输入: {user_input}
        对话历史: {history}
        
        请只返回JSON，不要其他内容。
        """.format(user_input=user_input, history=history_str)
        
        response = call_api(system_prompt=intent_prompt, user_prompt=user_prompt, temperature=temperature, max_tokens=max_tokens, model_name=model_name)
        print("====意图分析==== ", response)
        try:
            intent_data = json.loads(response)
            state["user_intent"] = intent_data.get("intent", "other")
            state["user_mood"] = intent_data.get("mood", "neutral")
            
        except:
            state["user_intent"] = "other"
            state["user_mood"] = "neutral"
        return state
    
    def _route_based_on_intent(self, state: AgentState) -> str:
        """根据意图路由到不同的处理节点"""
        intent = state.get("user_intent", "other")
        
        # 特殊意图需要专门处理
        special_intents = ["seeking_comfort", "goodbye"]
    
        if intent in special_intents:
            print("====特殊意图==== ", intent)
            return "special"
        else:
            print("====普通意图==== ", intent)
            return "normal"
    
    def _handle_special_case(self, state: AgentState) -> AgentState:
        """处理特殊情况的节点"""
        intent = state.get("user_intent", "other")
        mood = state.get("user_mood", "neutral")
        
        if intent == "seeking_comfort":
            # 添加安慰性的系统消息
            comfort_message = {
                "role": "system",
                "content": "用户需要安慰，请用温暖、支持性的语气回应，表达理解和关心。"
            }
            state["special_instruction"] = comfort_message
        
        print("====特殊节点==== ", state)
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """生成回应"""
        last_message = state["messages"][-1]
        user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

        mood = state.get("user_mood", "neutral")
        intent = state.get("user_intent", "other")
        history_str = "\n".join([f"{msg["role"]}: {msg["content"]}" for msg in state["conversation_history"][:-1]])
        special_instruction = state.get("special_instruction", {}).get("content", "")
        print("====生成回应-历史数据==== ", history_str)
        # 构建响应prompt -过往相关的参考信息: {last_information}
        response_prompt = """你是一个贴心的社交陪伴助手。"""
        user_input = """
        请根据以下信息回应用户：
        
        用户当前情绪: {mood}
        用户意图: {intent}
        当天的对话历史: {history}
        
        {special_instruction}
        
        请用自然、温暖、人性化的方式回应。保持对话流畅，展现同理心。
        
        用户输入: {user_input}
        
        你的回应:
        """.format(mood=mood, intent=intent, history=history_str, special_instruction=special_instruction, user_input=user_input)
        
        response = call_api(system_prompt=response_prompt, user_prompt=user_input, temperature=temperature, max_tokens=max_tokens, model_name=model_name)
        print("====生成回应==== ", response)
        # 添加AI回应到消息列表
        state["messages"].append(AIMessage(content=response))
        state["conversation_history"].append({"role": "ai", "content": response})
       
        return state
    
    def chat(self, user_input: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """主要聊天接口"""
        if conversation_history is None:
            conversation_history = []
        
        # 准备初始状态
        initial_state = AgentState(
            messages=[HumanMessage(content=user_input)],
            user_intent="",
            user_mood="neutral",
            conversation_history=conversation_history,
            needs_response=True
        )
        
        # 执行图
        final_state = self.graph.invoke(initial_state)
        print(final_state, len(final_state["messages"]))
        # 提取最后一条AI消息
        ai_response = final_state["messages"][-1].content if len(final_state["messages"]) > 1 else ""
        
        return ai_response

def main():
    agent = KAgent()
    
    # 测试对话
    test_messages = [
        "你好，我今天感觉有点孤单",
        "工作压力好大，不知道该怎么办",
        "我需要你的安慰",
        "谢谢你的倾听，我感觉好多了",
        "再见"
    ]

    test_messages_1 = [
        "今天是2025年吗"
    ]

    conversation_history = []
    for message in test_messages_1:
        print(f"用户: {message}")
        result = agent.chat(message, conversation_history)
        print("*-" * 50)

if __name__ == "__main__":
    main()