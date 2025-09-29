import gradio as gr
import time
import sys
sys.path.append('/mnt/projects/llm-server')
from src.agents.kagent import SocialCompanionAgent

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    agent = SocialCompanionAgent()
    conversation_history = []
    # 帮我补全代码，实现用户输入和机器人回复的交互
    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(history):
        user_message = history[-1][0]
        # 调用机器人回复函数
        bot_message = agent.chat(user_message, conversation_history)
        history[-1][1] = bot_message  # Update the history with bot's response
        return history
            
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)
demo.queue()
demo.launch(share=True)
