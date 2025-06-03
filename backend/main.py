from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import datetime
from pathlib import Path
import shutil
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken

# 加载环境变量
load_dotenv()

front_end_url = os.getenv("FRONT_END_URL", "http://localhost:3000")

app = FastAPI(title="AI剧本生成器", version="1.0.0")

# 添加CORS中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[front_end_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建uploads目录
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# 允许下载的文件类型
ALLOWED_FILES = {"character.txt", "story.txt", "generated.txt", "reasoning.txt"}

# 初始化OpenAI客户端
api_key = os.getenv("DEEPSEEK_API_KEY")
model = os.getenv("MODEL_NAME", "deepseek-chat")
temperature = float(os.getenv("TEMPERATURE", "0.7"))
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# 初始化tiktoken编码器
try:
    encoding = tiktoken.get_encoding("cl100k_base")  # 通用编码器
except:
    encoding = None

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

def count_tokens(text: str) -> int:
    """计算文本的token数量"""
    if encoding:
        return len(encoding.encode(text))
    else:
        # 如果tiktoken不可用，使用估算方式
        return int(len(text) / 1.5)

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
        
        # 检查token数量
        system_tokens = count_tokens(SCRIPT_PROMPT)
        user_tokens = count_tokens(user_content)
        estimated_tokens = system_tokens + user_tokens
        
        # 64K上下文限制检查
        if estimated_tokens > 64000:
            raise HTTPException(
                status_code=413, 
                detail=f"输入内容过长，估计使用{estimated_tokens}个tokens，超出64K上下文限制。请缩减人物小传或故事大纲的内容。"
            )
        
        # 调用AI生成剧本
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SCRIPT_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature,
            max_tokens=32000,  # 设置最大输出长度为32K
            stream=False
        )
        
        generated_script = response.choices[0].message.content
        reasoning_content = getattr(response.choices[0].message, 'reasoning_content', None)
        
        # 保存生成的剧本
        script_path = session_dir / "generated.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(generated_script)
        
        # 保存推理过程（如果存在）
        if reasoning_content:
            reasoning_path = session_dir / "reasoning.txt"
            with open(reasoning_path, "w", encoding="utf-8") as f:
                f.write(reasoning_content)
        
        return {
            "success": True,
            "session_id": request.session_id,
            "message": "剧本生成成功",
            "script_length": len(generated_script),
            "reasoning_length": len(reasoning_content) if reasoning_content else 0,
            "estimated_input_tokens": estimated_tokens,
            "has_reasoning": reasoning_content is not None,
            "files_generated": ["generated.txt"] + (["reasoning.txt"] if reasoning_content else []),
            "download_urls": {
                "script": f"/download/{request.session_id}/generated.txt",
                "reasoning": f"/download/{request.session_id}/reasoning.txt" if reasoning_content else None
            }
        }
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"剧本生成失败: {str(e)}")


@app.get("/download/{session_id}/{file_name}")
async def download_file(session_id: str, file_name: str):
    session_dir = UPLOADS_DIR / session_id
    
    # 检查session目录是否存在
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session ID不存在")
    
    # 检查文件是否存在
    if file_name not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail="不允许下载的文件类型")
    
    file_path = session_dir / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
