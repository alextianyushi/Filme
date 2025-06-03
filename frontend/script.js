// API配置
const API_BASE_URL = 'http://localhost:8000';

// DOM元素
const characterFile = document.getElementById('character-file');
const storyFile = document.getElementById('story-file');
const generateBtn = document.getElementById('generate-btn');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const errorSection = document.getElementById('error-section');

// 当前session信息
let currentSession = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 文件选择事件
    characterFile.addEventListener('change', handleFileSelect);
    storyFile.addEventListener('change', handleFileSelect);
    
    // 生成按钮事件
    generateBtn.addEventListener('click', generateScript);
    
    // 其他按钮事件
    document.getElementById('new-generation').addEventListener('click', resetForm);
    document.getElementById('retry-btn').addEventListener('click', generateScript);
    document.getElementById('download-script').addEventListener('click', () => downloadFile('generated.txt'));
    document.getElementById('download-reasoning').addEventListener('click', () => downloadFile('reasoning.txt'));
});

// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    const isCharacter = event.target.id === 'character-file';
    const infoElement = document.getElementById(isCharacter ? 'character-info' : 'story-info');
    const uploadItem = event.target.closest('.upload-item');
    
    if (file) {
        // 验证文件类型
        if (!file.name.endsWith('.txt')) {
            showError('请选择.txt格式的文件');
            event.target.value = '';
            return;
        }
        
        // 验证文件大小 (10MB)
        if (file.size > 10 * 1024 * 1024) {
            showError('文件大小不能超过10MB');
            event.target.value = '';
            return;
        }
        
        // 显示文件信息
        const sizeKB = (file.size / 1024).toFixed(1);
        infoElement.textContent = `✅ ${file.name} (${sizeKB} KB)`;
        uploadItem.classList.add('has-file');
    } else {
        infoElement.textContent = '';
        uploadItem.classList.remove('has-file');
    }
    
    // 检查是否可以生成
    checkCanGenerate();
}

// 检查是否可以生成剧本
function checkCanGenerate() {
    const hasCharacterFile = characterFile.files.length > 0;
    const hasStoryFile = storyFile.files.length > 0;
    generateBtn.disabled = !(hasCharacterFile && hasStoryFile);
}

// 生成剧本
async function generateScript() {
    try {
        hideAllSections();
        showProgress();
        
        // 第一步：上传文件
        const formData = new FormData();
        formData.append('character_file', characterFile.files[0]);
        formData.append('story_file', storyFile.files[0]);
        
        const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            const error = await uploadResponse.json();
            throw new Error(error.detail || '文件上传失败');
        }
        
        const uploadResult = await uploadResponse.json();
        currentSession = uploadResult.session_id;
        
        // 第二步：生成剧本
        const generateResponse = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSession
            })
        });
        
        if (!generateResponse.ok) {
            const error = await generateResponse.json();
            throw new Error(error.detail || '剧本生成失败');
        }
        
        const generateResult = await generateResponse.json();
        
        // 显示结果
        hideProgress();
        showResult(generateResult);
        
    } catch (error) {
        hideProgress();
        showError(error.message);
    }
}

// 显示进度
function showProgress() {
    progressSection.style.display = 'block';
    progressSection.classList.add('fade-in');
}

// 隐藏进度
function hideProgress() {
    progressSection.style.display = 'none';
}

// 显示结果
function showResult(result) {
    // 更新结果信息
    document.getElementById('session-id').textContent = result.session_id;
    document.getElementById('script-length').textContent = result.script_length.toLocaleString();
    document.getElementById('input-tokens').textContent = result.estimated_input_tokens.toLocaleString();
    
    // 推理过程信息
    const reasoningInfo = document.getElementById('reasoning-info');
    const downloadReasoning = document.getElementById('download-reasoning');
    
    if (result.has_reasoning) {
        document.getElementById('reasoning-length').textContent = result.reasoning_length.toLocaleString();
        reasoningInfo.style.display = 'flex';
        downloadReasoning.style.display = 'block';
    } else {
        reasoningInfo.style.display = 'none';
        downloadReasoning.style.display = 'none';
    }
    
    // 显示结果区域
    resultSection.style.display = 'block';
    resultSection.classList.add('fade-in');
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 显示错误
function showError(message) {
    document.getElementById('error-message').textContent = message;
    errorSection.style.display = 'block';
    errorSection.classList.add('fade-in');
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

// 隐藏所有结果区域
function hideAllSections() {
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    progressSection.style.display = 'none';
}

// 下载文件
async function downloadFile(filename) {
    if (!currentSession) {
        showError('没有可下载的文件');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/download/${currentSession}/${filename}`);
        
        if (!response.ok) {
            throw new Error('下载失败');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        showError('下载失败：' + error.message);
    }
}

// 重置表单
function resetForm() {
    // 清空文件输入
    characterFile.value = '';
    storyFile.value = '';
    
    // 清空文件信息
    document.getElementById('character-info').textContent = '';
    document.getElementById('story-info').textContent = '';
    
    // 移除样式
    document.querySelectorAll('.upload-item').forEach(item => {
        item.classList.remove('has-file');
    });
    
    // 隐藏结果区域
    hideAllSections();
    
    // 重置按钮状态
    generateBtn.disabled = true;
    
    // 清空session
    currentSession = null;
    
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 