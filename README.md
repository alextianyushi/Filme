# AI Script Generator MVP

## Product Positioning
Input character profiles and story outlines to generate professional film scripts with AI.

## Core Features
1. **File Upload** - Upload character profiles and story outlines (supports .txt format only)
2. **AI Generation** - Generate standard script format based on DeepSeek API
3. **Result Output** - Online preview, download txt files, copy text

## User Interface
```
📝 Character profile file upload (.txt)
📖 Story outline file upload (.txt)
🚀 Generate professional script button
📄 Result display and download (.txt)
```

## Quick Start

### Prerequisites
- Python 3.13+
- DeepSeek API Key
- Modern browser

### Backend Setup

1. **Enter backend directory**
```bash
cd backend
```

2. **Install dependencies**
```bash
# Using uv (recommended)
uv sync
```

3. **Configure environment variables**
```bash
# Create .env file
cp .env.example .env

# Edit .env file, add your API key
DEEPSEEK_API_KEY=your_deepseek_api_key_here
MODEL_NAME=deepseek-reasoner
TEMPERATURE=1.3
FRONT_END_URL=http://localhost:3000
```

4. **Start backend server**
```bash
# Development mode
uv run main.py
```

Backend will start at `http://localhost:8000`

### Frontend Setup

1. **Enter frontend directory**
```bash
cd frontend
```

2. **Configure API address**
```bash
# Copy config file
cp config.example.js config.js

# Edit config.js, set backend address
window.CONFIG = {
    BACKEND_URL: 'http://localhost:8000'  // Local development
    // Or use your backend address
};
```

3. **Start frontend server**
```bash
# Using Python built-in server
python3 -m http.server 3000

# Or directly open index.html in browser
open index.html
```

Frontend will start at `http://localhost:3000`

## Technical Architecture

### Frontend
- HTML + CSS + JavaScript
- File upload component
- Responsive design

### Backend
- FastAPI
- 3 API endpoints:
  - `POST /upload` - File upload
  - `POST /generate` - Script generation
  - `GET /download/{session_id}/{filename}` - Download files

### AI Integration
- DeepSeek API
- Standard script format prompts

### File Formats
- Input: .txt plain text files only
- Output: .txt plain text format

## User Workflow
1. Prepare character profile.txt and story outline.txt
2. Upload both files
3. Click generate script
4. Wait for AI generation (usually 1-3 minutes)
5. Download result files

## Deployment
- Frontend: GitHub Pages
- Backend: Fly.io