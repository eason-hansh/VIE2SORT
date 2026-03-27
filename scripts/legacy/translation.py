import os
from dashscope import Generation
import dashscope

dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"请将以下内容翻译为中文："
                                f"Máy 1 thiết bị bất thường. Máy 1 thiết bị"},
]
response = Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key = "sk-xxx",
    # api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_key="sk-33e07c61f66d4a76a429824c7e394117",
    model="qwen3-max",
    messages=messages,
    result_format="message",
    # 开启深度思考
    enable_thinking=False,
)

if response.status_code == 200:
    # enable_thinking=False 时，reasoning_content 可能不存在
    print("=" * 20 + "完整回复" + "=" * 20)
    print(response.output.choices[0].message.content)
else:
    print(f"HTTP返回码：{response.status_code}")
    print(f"错误码：{response.code}")
    print(f"错误信息：{response.message}")
