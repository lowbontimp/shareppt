// File upload handling
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('file');
const dropZone = document.getElementById('dropZone');
const messageDiv = document.getElementById('uploadMessage');

// Drag and drop functionality
if (dropZone) {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('drop-zone-active');
    }

    function unhighlight(e) {
        dropZone.classList.remove('drop-zone-active');
    }

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            // Create a new FileList-like object and assign to input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            fileInput.files = dataTransfer.files;
            updateDropZoneText(files[0].name);
        }
    }

    // Handle file input change
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                updateDropZoneText(e.target.files[0].name);
            }
        });
    }

    function updateDropZoneText(fileName) {
        const dropZoneContent = dropZone.querySelector('.drop-zone-content');
        if (dropZoneContent) {
            dropZoneContent.innerHTML = `<p class="drop-zone-text">선택된 파일: <strong>${fileName}</strong></p>`;
        }
    }
}

// Utility function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Utility function to format speed
function formatSpeed(bytesPerSecond) {
    return formatFileSize(bytesPerSecond) + '/s';
}

if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!fileInput || !fileInput.files[0]) {
            if (messageDiv) {
                showMessage(messageDiv, '파일을 선택해주세요.', 'error');
            }
            return;
        }
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        // Add CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            formData.append('csrf_token', csrfToken);
        }
        
        // Get progress elements
        const progressDiv = document.getElementById('uploadProgress');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const progressPercent = document.getElementById('progressPercent');
        const progressBytes = document.getElementById('progressBytes');
        const progressSpeed = document.getElementById('progressSpeed');
        const uploadButton = document.getElementById('uploadButton');
        
        // Show progress bar and hide message
        if (progressDiv) {
            progressDiv.style.display = 'block';
        }
        if (messageDiv) {
            messageDiv.textContent = '';
            messageDiv.className = 'message';
        }
        
        // Disable upload button
        if (uploadButton) {
            uploadButton.disabled = true;
            uploadButton.textContent = '업로드 중...';
        }
        
        // Initialize progress
        let startTime = Date.now();
        let lastLoaded = 0;
        let lastTime = startTime;
        
        // Create XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();
        const basePath = window.APP_BASE_PATH || '/share';
        
        // Update progress
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                const currentTime = Date.now();
                const elapsed = (currentTime - lastTime) / 1000; // seconds
                const loaded = e.loaded - lastLoaded;
                const speed = elapsed > 0 ? loaded / elapsed : 0;
                
                // Update progress bar
                if (progressBar) {
                    progressBar.style.width = percent + '%';
                }
                if (progressPercent) {
                    progressPercent.textContent = percent + '%';
                }
                if (progressBytes) {
                    progressBytes.textContent = formatFileSize(e.loaded) + ' / ' + formatFileSize(e.total);
                }
                if (progressSpeed && speed > 0) {
                    progressSpeed.textContent = formatSpeed(speed);
                }
                
                lastLoaded = e.loaded;
                lastTime = currentTime;
            }
        });
        
        // Handle completion
        xhr.addEventListener('load', function() {
            if (progressDiv) {
                progressDiv.style.display = 'none';
            }
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = '업로드';
            }
            
            // Handle 401 Unauthorized
            if (xhr.status === 401) {
                showMessage(messageDiv, '로그인이 필요합니다. 페이지를 새로고침하고 로그인해주세요.', 'error');
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
                return;
            }
            
            // Handle 413 Payload Too Large
            if (xhr.status === 413) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    showMessage(messageDiv, data.error || '파일 크기가 너무 큽니다. 최대 10GB까지 업로드할 수 있습니다.', 'error');
                } catch (e) {
                    showMessage(messageDiv, '파일 크기가 10GB를 초과합니다. 최대 10GB까지 업로드할 수 있습니다.', 'error');
                }
                return;
            }
            
            // Parse response
            try {
                const data = JSON.parse(xhr.responseText);
                
                if (xhr.status >= 200 && xhr.status < 300 && data.success) {
                    showMessage(messageDiv, '파일이 성공적으로 업로드되었습니다.', 'success');
                    fileInput.value = '';
                    // Reset drop zone text
                    if (dropZone) {
                        const dropZoneContent = dropZone.querySelector('.drop-zone-content');
                        if (dropZoneContent) {
                            dropZoneContent.innerHTML = `
                                <p class="drop-zone-text">파일을 여기에 드래그&드롭하거나</p>
                                <p class="drop-zone-text">아래 버튼을 클릭하여 선택하세요</p>
                            `;
                        }
                    }
                    // Reload page after short delay to show new file
                    setTimeout(() => {
                        window.location.reload(true);
                    }, 500);
                } else {
                    showMessage(messageDiv, data.error || '업로드에 실패했습니다.', 'error');
                }
            } catch (e) {
                showMessage(messageDiv, '서버 오류가 발생했습니다. 서버 로그를 확인해주세요.', 'error');
                console.error('Parse error:', e, xhr.responseText);
            }
        });
        
        // Handle errors
        xhr.addEventListener('error', function() {
            if (progressDiv) {
                progressDiv.style.display = 'none';
            }
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = '업로드';
            }
            showMessage(messageDiv, '업로드 중 네트워크 오류가 발생했습니다.', 'error');
        });
        
        // Handle abort
        xhr.addEventListener('abort', function() {
            if (progressDiv) {
                progressDiv.style.display = 'none';
            }
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = '업로드';
            }
        });
        
        // Send request
        xhr.open('POST', `${basePath}/upload`);
        xhr.send(formData);
    });
}

// Delete file function
function deleteFile(fileId, fileName) {
    if (!confirm(`"${fileName}" 파일을 삭제하시겠습니까?`)) {
        return;
    }
    
    const basePath = window.APP_BASE_PATH || '/share';
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    fetch(`${basePath}/delete/${fileId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken || ''
        }
    })
    .then(async response => {
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error('서버 오류가 발생했습니다.');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('파일이 성공적으로 삭제되었습니다.');
            window.location.reload();
        } else {
            alert(data.error || '삭제에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        alert('삭제 중 오류가 발생했습니다: ' + error.message);
    });
}

// Login form handling - simple plain text password submission
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        
        if (!usernameInput.value || !passwordInput.value) {
            e.preventDefault();
            alert('아이디와 비밀번호를 입력해주세요.');
            return;
        }
        
        // Submit form with plain text password (no client-side hashing)
        // Form will submit normally
    });
}

// Add event listeners to delete buttons
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileId = this.getAttribute('data-file-id');
            const fileName = this.getAttribute('data-file-name');
            deleteFile(fileId, fileName);
        });
    });
});

// Utility function to show messages
function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `message ${type}`;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            element.textContent = '';
            element.className = 'message';
        }, 5000);
    }
}


