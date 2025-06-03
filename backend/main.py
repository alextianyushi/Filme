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

# Load environment variables
load_dotenv()

front_end_url = os.getenv("FRONT_END_URL", "http://localhost:3000")

app = FastAPI(title="AI Script Generator", version="1.0.0")

# Add CORS middleware to allow frontend cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[front_end_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Allowed file types for download
ALLOWED_FILES = {"character.txt", "story.txt", "generated.txt", "reasoning.txt"}

# Initialize OpenAI client
api_key = os.getenv("DEEPSEEK_API_KEY")
model = os.getenv("MODEL_NAME", "deepseek-chat")
temperature = float(os.getenv("TEMPERATURE", "0.7"))
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Initialize tiktoken encoder
try:
    encoding = tiktoken.get_encoding("cl100k_base")  # Universal encoder
except:
    encoding = None

# Load script generation prompt from file
def load_script_prompt():
    prompt_path = Path("prompts/script_prompt.txt")
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        # If file doesn't exist, raise error
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

SCRIPT_PROMPT = load_script_prompt()

def count_tokens(text: str) -> int:
    """Calculate the number of tokens in the text"""
    if encoding:
        return len(encoding.encode(text))
    else:
        # If tiktoken is not available, use estimation
        return int(len(text) / 1.5)

class GenerateRequest(BaseModel):
    session_id: str


@app.get("/")
async def root():
    return {"message": "AI Script Generator API"}


@app.post("/upload")
async def upload_files(
    character_file: UploadFile = File(..., description="Character profile file"),
    story_file: UploadFile = File(..., description="Story outline file")
):
    # Validate file format
    if not character_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Character profile file must be in .txt format")
    
    if not story_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Story outline file must be in .txt format")
    
    # Create timestamp session ID
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = UPLOADS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    
    try:
        # Save character profile file
        character_path = session_dir / "character.txt"
        with open(character_path, "wb") as f:
            shutil.copyfileobj(character_file.file, f)
        
        # Save story outline file
        story_path = session_dir / "story.txt"
        with open(story_path, "wb") as f:
            shutil.copyfileobj(story_file.file, f)
        
        # Get file sizes
        character_size = character_path.stat().st_size
        story_size = story_path.stat().st_size
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Files uploaded successfully",
            "files": {
                "character": f"character.txt ({character_size} bytes)",
                "story": f"story.txt ({story_size} bytes)"
            }
        }
    
    except Exception as e:
        # If error occurs, clean up created directory
        if session_dir.exists():
            shutil.rmtree(session_dir)
        raise HTTPException(status_code=500, detail=f"Failed to save files: {str(e)}")


@app.post("/generate")
async def generate_script(request: GenerateRequest):
    session_dir = UPLOADS_DIR / request.session_id
    
    # Check if session directory exists
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session ID does not exist")
    
    character_path = session_dir / "character.txt"
    story_path = session_dir / "story.txt"
    
    # Check if files exist
    if not character_path.exists() or not story_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded files are incomplete")
    
    try:
        # Read character profile and story outline
        with open(character_path, "r", encoding="utf-8") as f:
            character_content = f.read().strip()
        
        with open(story_path, "r", encoding="utf-8") as f:
            story_content = f.read().strip()
        
        # Build user input content
        user_content = f"""Character Profile:
{character_content}

Story Outline:
{story_content}

Please create a complete film script based on the above character profile and story outline."""
        
        # Check token count
        system_tokens = count_tokens(SCRIPT_PROMPT)
        user_tokens = count_tokens(user_content)
        estimated_tokens = system_tokens + user_tokens
        
        # 64K context limit check
        if estimated_tokens > 64000:
            raise HTTPException(
                status_code=413, 
                detail=f"Input content too long, estimated {estimated_tokens} tokens, exceeds 64K context limit. Please reduce the content of character profile or story outline."
            )
        
        # Call AI to generate script
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SCRIPT_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature,
            max_tokens=32000,  # Set maximum output length to 32K
            stream=False
        )
        
        generated_script = response.choices[0].message.content
        reasoning_content = getattr(response.choices[0].message, 'reasoning_content', None)
        
        # Save generated script
        script_path = session_dir / "generated.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(generated_script)
        
        # Save reasoning process (if exists)
        if reasoning_content:
            reasoning_path = session_dir / "reasoning.txt"
            with open(reasoning_path, "w", encoding="utf-8") as f:
                f.write(reasoning_content)
        
        return {
            "success": True,
            "session_id": request.session_id,
            "message": "Script generated successfully",
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
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate script: {str(e)}")


@app.get("/download/{session_id}/{file_name}")
async def download_file(session_id: str, file_name: str):
    session_dir = UPLOADS_DIR / session_id
    
    # Check if session directory exists
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session ID does not exist")
    
    # Check if file type is allowed
    if file_name not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail="File type not allowed for download")
    
    file_path = session_dir / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File does not exist")
    
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
