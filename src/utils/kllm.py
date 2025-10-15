import requests
import json

def call_api(system_prompt, user_prompt, temperature, max_tokens, model_name):
    """
    异步调用 openai形式 API
    
    参数:
    - prompt: 输入的提示文本
    - temperature: 生成温度 (0.1-1.0)
    - max_tokens: 最大生成token数
    
    返回:
    - 生成的文本响应
    """
    
    url = "http://localhost:8080/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None
    except KeyError as e:
        print(f"解析响应错误: {e}")
        print(f"完整响应: {response.text}")
        return None
    except Exception as e:
        print(f"其他错误: {e}")
        return None

def call_api_stream(system_prompt, user_prompt, temperature, max_tokens, model_name):
    """
    流式调用 openai形式 API
    
    参数:
    - prompt: 输入的提示文本
    - temperature: 生成温度 (0.1-1.0)
    - max_tokens: 最大生成token数
    
    返回:
    - 生成器，每次yield一个token
    """
    
    url = "http://localhost:8080/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    data = decoded_line[6:]
                    if data != '[DONE]':
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        yield None
    except Exception as e:
        print(f"其他错误: {e}")
        yield None
        
# 非流式使用示例
def main():
    system_prompt = "请回答用户的问题"
    user_prompt = "你好，你是谁"
    temperature = 0.1
    max_tokens = 32768
    model_name = "ggml-model-fp16"
    
    response = call_api(system_prompt, user_prompt, temperature, max_tokens, model_name)
    
    if response:
        print("模型响应:")
        print(response)
    else:
        print("调用失败")

# 流式使用示例
def main_stream():
    system_prompt = "请回答用户的问题"
    user_prompt = "请给我讲个故事"
    temperature = 0.1
    max_tokens = 20000
    model_name = "qwen3-4b-instruct-2507-fp8"   
    # qwen3-4b-instruct-2507-fp8
    # ggml-model-fp16
    
    for chunk in call_api_stream(system_prompt, user_prompt, temperature, max_tokens, model_name):
        if chunk:
            print(chunk, end='', flush=True)

# 使用示例
if __name__ == "__main__":
    main_stream()