from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import datetime
from pathlib import Path
import shutil

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
