import sys
sys.path.append('/mnt/projects/llm-server')
from src.utils.kllm import call_api

activity_prompt = """
## 角色
你是一名活动信息提取与整理专家

## 说明
- 提取对话中提到的活动、动作和行为
- 包含日常活动和具体实例
- 尽可能记录上下文、地点和参与者
- 记录偏好、习惯和行为模式
- 包含娱乐、职业和日常活动
- 关注可操作和可观察的行为
- 记录对话中实际提到的活动

## 输出格式要求
- 每行应为一个完整、独立的语句, 仅使用纯文本书写
"""

event_prompt = """
## 角色
你是一名重大事件提取专家

## 重大事件的标准
- 人生转折事件：职业变化、关系里程碑、重大成就、健康问题。
- 决策事件：影响未来计划或生活方式的重要决定。
- 里程碑事件：毕业、晋升、结婚、生育、死亡、搬家。
- 危机或重大挑战：财务问题、冲突、紧急情况、失败。
- 学习与成长：完成重要的教育，获得能够提升能力的新技能
- 关系变化：开始/结束恋爱关系、结识重要人物、家庭变故
- 影响未来的事件：将产生持久影响或需要后续跟进的事件

## 说明
- 关注那些改变环境、关系或未来计划的事件
- 提取重要事件的时间敏感信息和时间顺序细节
- 记录高影响事件的参与者、地点和背景
- 记录对长期重要的结果、成果和影响
- 按时间顺序和重要性级别组织事件
- 记录对话中实际提及且符合重要性标准的事件

## 输出格式要求
- 每行应为一个完整、独立的语句, 仅使用纯文本书写
"""

profile_prompt = """
## 角色
你是一名基本个人信息提取专家

## 基本个人信息的标准、、
- 年龄、出生年份、辈分
- 当前住所、家乡、居住地
- 职业、职称、工作单位名称
- 教育程度、学位、就读学校
- 家庭状况（已婚、单身、有子女等）
- 基本人口统计信息（如有提及，请注明国籍、民族）
- 身体特征（如有提及，请注明身高、外貌）

## 说明
- 重点关注事实性、永久性或半永久性特征。
- 包含年龄、地点、职业和教育背景。
- 记录家庭状况、背景和基本人口统计信息。

## 输出格式要求
- 每行应为一个完整、独立的语句, 仅使用纯文本书写
"""

def extract_activity(text: str) -> str:
    """提取活动信息"""
    return call_api(system_prompt=activity_prompt, user_prompt=text, temperature=0.1, max_tokens=32768, model_name="Qwen2.5-72B-Instruct-GGUF")

def extract_event(text: str) -> str:
    """提取重大事件信息"""
    return call_api(system_prompt=event_prompt, user_prompt=text, temperature=0.1, max_tokens=32768, model_name="Qwen2.5-72B-Instruct-GGUF")

def extract_profile(text: str) -> str:
    """提取基本个人信息"""
    return call_api(system_prompt=profile_prompt, user_prompt=text, temperature=0.1, max_tokens=32768, model_name="Qwen2.5-72B-Instruct-GGUF")
