// Simple frontend that works directly with block-storage (no auth required)
const BLOCK_STORAGE_URL = 'http://localhost:8003';

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const filesList = document.getElementById('filesList');

// Store uploaded files
let uploadedFiles = [];

// Initialize the frontend
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadUploadedFiles();
});

function setupEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Click to browse
    uploadArea.addEventListener('click', () => fileInput.click());
}

function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
        uploadFiles(files);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) {
        uploadFiles(files);
    }
}

async function uploadFiles(files) {
    for (const file of files) {
        await uploadSingleFile(file);
    }
}

async function uploadSingleFile(file) {
    // Show progress
    uploadProgress.style.display = 'block';
    progressText.textContent = `Uploading ${file.name}...`;
    
    // Add file to list with uploading status
    const fileId = Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    addFileToList(file, fileId, 'uploading');
    
    try {
        // Simple upload directly to block-storage
        const formData = new FormData();
        formData.append('file', file);
        formData.append('chunk_id', fileId);
        
        const response = await fetch(`${BLOCK_STORAGE_URL}/chunks`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Update file status to success
        updateFileStatus(fileId, 'success');
        
        // Store file info
        uploadedFiles.push({
            id: fileId,
            name: file.name,
            size: file.size,
            uploadedAt: new Date().toISOString(),
            chunkId: result.chunk_id || fileId
        });
        
        // Save to localStorage
        localStorage.setItem('uploadedFiles', JSON.stringify(uploadedFiles));
        
        progressText.textContent = `${file.name} uploaded successfully!`;
        
    } catch (error) {
        console.error('Upload error:', error);
        updateFileStatus(fileId, 'error');
        progressText.textContent = `Failed to upload ${file.name}`;
    }
    
    // Hide progress after 2 seconds
    setTimeout(() => {
        uploadProgress.style.display = 'none';
        progressFill.style.width = '0%';
    }, 2000);
    
    // Reset progress
    progressFill.style.width = '100%';
}

function addFileToList(file, fileId, status) {
    // Remove "no files" message
    const noFilesMsg = filesList.querySelector('.no-files');
    if (noFilesMsg) {
        noFilesMsg.remove();
    }
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.id = `file-${fileId}`;
    
    fileItem.innerHTML = `
        <div class="file-info">
            <span class="file-icon">📄</span>
            <div>
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
        </div>
        <div class="file-status status-${status}" id="status-${fileId}">
            ${getStatusText(status)}
        </div>
    `;
    
    filesList.appendChild(fileItem);
}

function updateFileStatus(fileId, status) {
    const statusElement = document.getElementById(`status-${fileId}`);
    if (statusElement) {
        statusElement.className = `file-status status-${status}`;
        statusElement.textContent = getStatusText(status);
    }
}

function getStatusText(status) {
    switch (status) {
        case 'uploading': return 'Uploading...';
        case 'success': return 'Uploaded';
        case 'error': return 'Failed';
        default: return 'Unknown';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function loadUploadedFiles() {
    const savedFiles = localStorage.getItem('uploadedFiles');
    if (savedFiles) {
        uploadedFiles = JSON.parse(savedFiles);
        
        // Display saved files
        uploadedFiles.forEach(file => {
            const fileObj = { name: file.name, size: file.size };
            addFileToList(fileObj, file.id, 'success');
        });
    }
}

// Test connection to block-storage on load
fetch(`${BLOCK_STORAGE_URL}/health`)
    .then(response => {
        if (!response.ok) {
            console.warn('Block storage service not available');
        }
    })
    .catch(error => {
        console.warn('Cannot connect to block storage service:', error);
    });
