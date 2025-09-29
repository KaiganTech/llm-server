import requests
import json
import os

response = requests.post(
    "http://127.0.0.1:10001/ask",
    json={"message": "你能做些什么"}
)
print(response.json())

