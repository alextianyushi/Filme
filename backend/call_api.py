from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
model = os.getenv("MODEL_NAME", "deepseek-chat")
temperature = float(os.getenv("TEMPERATURE","0.7"))

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "你是一个专业的剧本创作助手，所有的文字都是镜头可以表现出来的动作，景色，杜绝抽象描写，尽量避免不必要的配角。"},
        {"role": "user", "content": "一个男生想邀请心仪的女生去看电影，请帮我写一个场景的剧本，不超过三百字。"},
    ],
    stream=False
)

print(response.choices[0].message.content)