# AI剧本生成器 MVP

## 产品定位
输入人物小传和故事大纲，AI生成专业影视剧本。

## 核心功能
1. **文件上传** - 上传人物小传和故事大纲（仅支持.txt格式）
2. **AI生成** - 基于DeepSeek API生成标准剧本格式
3. **结果输出** - 在线预览、下载txt文件、复制文本

## 用户界面
```
📝 人物小传文件上传 (.txt)
📖 故事大纲文件上传 (.txt)
🚀 生成专业剧本按钮
📄 结果显示和下载 (.txt)
```

## 快速启动

### 前置要求
- Python 3.13+
- DeepSeek API Key
- 现代浏览器

### 后端启动

1. **进入后端目录**
```bash
cd backend
```

2. **安装依赖**
```bash
# 使用 uv （推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，添加你的API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here
MODEL_NAME=deepseek-chat
TEMPERATURE=0.7
FRONT_END_URL=http://localhost:3000
```

4. **启动后端服务器**
```bash
# 开发模式
uv run main.py
```

后端将在 `http://localhost:8000` 启动

### 前端启动

1. **进入前端目录**
```bash
cd frontend
```

2. **配置API地址**
```bash
# 复制配置文件
cp config.example.js config.js

# 编辑 config.js，设置后端地址
window.CONFIG = {
    BACKEND_URL: 'http://localhost:8000'  // 本地开发
    // 或者使用你的后端地址
};
```

3. **启动前端服务器**
```bash
# 使用 Python 内置服务器
python3 -m http.server 3000

# 或直接用浏览器打开 index.html
open index.html
```

前端将在 `http://localhost:3000` 启动

## 技术架构

### 前端
- HTML + CSS + JavaScript
- 文件上传组件
- 响应式设计

### 后端
- FastAPI
- 3个API接口：
  - `POST /upload` - 文件上传
  - `POST /generate` - 剧本生成
  - `GET /download/{session_id}/{filename}` - 下载文件

### AI集成
- DeepSeek API
- 标准剧本格式prompt

### 文件格式
- 输入：仅支持.txt纯文本文件
- 输出：.txt纯文本格式

## 用户流程
1. 准备人物小传.txt和故事大纲.txt
2. 上传两个文件
3. 点击生成剧本
4. 等待AI生成（通常1-3分钟）
5. 下载结果文件

## 部署方案
- 前端：GitHub Pages
- 后端：

## 故障排除

### 常见问题

1. **后端启动失败**
   - 检查Python版本是否为3.13+
   - 确认所有依赖已正确安装
   - 检查.env文件是否存在且配置正确

2. **前端无法连接后端**
   - 检查config.js中的BACKEND_URL是否正确
   - 确认后端服务正在运行
   - 检查CORS设置

3. **文件上传失败**
   - 确认文件格式为.txt
   - 检查文件大小不超过10MB
   - 确认DeepSeek API密钥有效

## MVP验证目标
- 需求验证：用户是否需要AI剧本生成
- 质量验证：生成剧本是否可用
- 流程验证：操作流程是否顺畅