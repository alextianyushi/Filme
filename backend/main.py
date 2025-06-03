from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import datetime
from pathlib import Path
import shutil
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="AI剧本生成器", version="1.0.0")

# 添加CORS中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建uploads目录
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# 初始化OpenAI客户端
api_key = os.getenv("DEEPSEEK_API_KEY")
model = os.getenv("MODEL_NAME", "deepseek-chat")
temperature = float(os.getenv("TEMPERATURE", "0.7"))
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# 从文件读取剧本生成prompt
def load_script_prompt():
    prompt_path = Path("prompts/script_prompt.txt")
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        # 如果文件不存在，抛出错误
        raise FileNotFoundError(f"Prompt文件不存在: {prompt_path}")

SCRIPT_PROMPT = load_script_prompt()


class GenerateRequest(BaseModel):
    session_id: str


@app.get("/")
async def root():
    return {"message": "AI剧本生成器 API"}


@app.post("/upload")
async def upload_files(
    character_file: UploadFile = File(..., description="人物小传文件"),
    story_file: UploadFile = File(..., description="故事大纲文件")
):
    # 验证文件格式
    if not character_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="人物小传文件必须是.txt格式")
    
    if not story_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="故事大纲文件必须是.txt格式")
    
    # 创建timestamp会话ID
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = UPLOADS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    
    try:
        # 保存人物小传文件
        character_path = session_dir / "character.txt"
        with open(character_path, "wb") as f:
            shutil.copyfileobj(character_file.file, f)
        
        # 保存故事大纲文件
        story_path = session_dir / "story.txt"
        with open(story_path, "wb") as f:
            shutil.copyfileobj(story_file.file, f)
        
        # 获取文件大小
        character_size = character_path.stat().st_size
        story_size = story_path.stat().st_size
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "文件上传成功",
            "files": {
                "character": f"character.txt ({character_size} bytes)",
                "story": f"story.txt ({story_size} bytes)"
            }
        }
    
    except Exception as e:
        # 如果出错，清理已创建的目录
        if session_dir.exists():
            shutil.rmtree(session_dir)
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


@app.post("/generate")
async def generate_script(request: GenerateRequest):
    session_dir = UPLOADS_DIR / request.session_id
    
    # 检查session目录是否存在
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session ID不存在")
    
    character_path = session_dir / "character.txt"
    story_path = session_dir / "story.txt"
    
    # 检查文件是否存在
    if not character_path.exists() or not story_path.exists():
        raise HTTPException(status_code=404, detail="上传的文件不完整")
    
    try:
        # 读取人物小传和故事大纲
        with open(character_path, "r", encoding="utf-8") as f:
            character_content = f.read().strip()
        
        with open(story_path, "r", encoding="utf-8") as f:
            story_content = f.read().strip()
        
        # 构建用户输入内容
        user_content = f"""人物小传：
{character_content}

故事大纲：
{story_content}

请基于以上人物小传和故事大纲，创作一个完整的影视剧本。"""
        
        # 调用AI生成剧本
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SCRIPT_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature,
            stream=False
        )
        
        generated_script = response.choices[0].message.content
        
        # 保存生成的剧本
        script_path = session_dir / "generated.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(generated_script)
        
        return {
            "success": True,
            "session_id": request.session_id,
            "message": "剧本生成成功",
            "script": generated_script,
            "script_length": len(generated_script)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"剧本生成失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
