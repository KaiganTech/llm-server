import json

current_day_note_path = "/mnt/projects/llm-server/src/diary_system/current_day_history.json"
with open(current_day_note_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(data['conversation_history'])
