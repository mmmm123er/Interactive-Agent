from openai import OpenAI
import os
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["all_proxy"] = ""

client = OpenAI(
    api_key="sk-ws-H.EMIRERR.bA5w.MEQCIDvj39oMBiqg18GVQixR1NIhAdjexgCs1JWCFmTqjy3VAiBI0B0YmZn77q_fOHIlGF3cGxqAbZqZbctO_cYGyGzm0A",
    base_url="https://llm-ip9z9mhyy19015m0.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.5/demo/CI_Demo/mathv-1327.jpg"
                }
            },
            {
                "type": "text",
                "text": "图里是什么"
            }
        ]
    }
]


chat_response = client.chat.completions.create(
    model="qwen3.6-flash",
    messages=messages,
    max_tokens=20480,
    temperature=1.0,
    top_p=0.95,
    presence_penalty=0.0,
    extra_body={
        "enable_thinking": False,
    }, 
    stream=True,  # 启用流式输出
)

# 处理流式响应
full_response = ""
for chunk in chat_response:
    if chunk.choices and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # 实时打印内容
        full_response += content

print()  # 打印换行符

