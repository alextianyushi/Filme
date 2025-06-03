// API configuration
const API_BASE_URL = window.CONFIG?.BACKEND_URL || 'http://localhost:8000';

// DOM elements
const characterFile = document.getElementById('character-file');
const storyFile = document.getElementById('story-file');
const generateBtn = document.getElementById('generate-btn');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const errorSection = document.getElementById('error-section');

// Current session information
let currentSession = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // File selection events
    characterFile.addEventListener('change', handleFileSelect);
    storyFile.addEventListener('change', handleFileSelect);
    
    // Generate button event
    generateBtn.addEventListener('click', generateScript);
    
    // Other button events
    document.getElementById('new-generation').addEventListener('click', resetForm);
    document.getElementById('retry-btn').addEventListener('click', generateScript);
    document.getElementById('download-script').addEventListener('click', () => downloadFile('generated.txt'));
    document.getElementById('download-reasoning').addEventListener('click', () => downloadFile('reasoning.txt'));
});

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    const isCharacter = event.target.id === 'character-file';
    const infoElement = document.getElementById(isCharacter ? 'character-info' : 'story-info');
    const uploadItem = event.target.closest('.upload-item');
    
    if (file) {
        // Validate file type
        if (!file.name.endsWith('.txt')) {
            showError('Please select a .txt format file');
            event.target.value = '';
            return;
        }
        
        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            showError('File size cannot exceed 10MB');
            event.target.value = '';
            return;
        }
        
        // Display file information
        const sizeKB = (file.size / 1024).toFixed(1);
        infoElement.textContent = `✅ ${file.name} (${sizeKB} KB)`;
        uploadItem.classList.add('has-file');
    } else {
        infoElement.textContent = '';
        uploadItem.classList.remove('has-file');
    }
    
    // Check if generation is possible
    checkCanGenerate();
}

// Check if script generation is possible
function checkCanGenerate() {
    const hasCharacterFile = characterFile.files.length > 0;
    const hasStoryFile = storyFile.files.length > 0;
    generateBtn.disabled = !(hasCharacterFile && hasStoryFile);
}

// Generate script
async function generateScript() {
    try {
        hideAllSections();
        showProgress();
        
        // Step 1: Upload files
        const formData = new FormData();
        formData.append('character_file', characterFile.files[0]);
        formData.append('story_file', storyFile.files[0]);
        
        const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            const error = await uploadResponse.json();
            throw new Error(error.detail || 'File upload failed');
        }
        
        const uploadResult = await uploadResponse.json();
        currentSession = uploadResult.session_id;
        
        // Step 2: Generate script
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
            throw new Error(error.detail || 'Script generation failed');
        }
        
        const generateResult = await generateResponse.json();
        
        // Display results
        hideProgress();
        showResult(generateResult);
        
    } catch (error) {
        hideProgress();
        showError(error.message);
    }
}

// Show progress
function showProgress() {
    progressSection.style.display = 'block';
    progressSection.classList.add('fade-in');
}

// Hide progress
function hideProgress() {
    progressSection.style.display = 'none';
}

// Show results
function showResult(result) {
    // Update result information
    document.getElementById('session-id').textContent = result.session_id;
    document.getElementById('script-length').textContent = result.script_length.toLocaleString();
    document.getElementById('input-tokens').textContent = result.estimated_input_tokens.toLocaleString();
    
    // Reasoning process information
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
    
    // Display result section
    resultSection.style.display = 'block';
    resultSection.classList.add('fade-in');
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// Show error
function showError(message) {
    document.getElementById('error-message').textContent = message;
    errorSection.style.display = 'block';
    errorSection.classList.add('fade-in');
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

// Hide all result sections
function hideAllSections() {
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    progressSection.style.display = 'none';
}

// Download file
async function downloadFile(filename) {
    if (!currentSession) {
        showError('No file available for download');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/download/${currentSession}/${filename}`);
        
        if (!response.ok) {
            throw new Error('Download failed');
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
        showError('Download failed: ' + error.message);
    }
}

// Reset form
function resetForm() {
    // Clear file inputs
    characterFile.value = '';
    storyFile.value = '';
    
    // Clear file information
    document.getElementById('character-info').textContent = '';
    document.getElementById('story-info').textContent = '';
    
    // Remove styles
    document.querySelectorAll('.upload-item').forEach(item => {
        item.classList.remove('has-file');
    });
    
    // Hide result sections
    hideAllSections();
    
    // Reset button state
    generateBtn.disabled = true;
    
    // Clear session
    currentSession = null;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Utility function: Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 