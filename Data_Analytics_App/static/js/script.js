// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const analyzeBtn = document.getElementById('analyzeBtn');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');
const statsGrid = document.getElementById('statsGrid');
const numericSummary = document.getElementById('numericSummary');
const visualizationsContent = document.getElementById('visualizationsContent');
const aiInsightsContent = document.getElementById('aiInsightsContent');
const modelSelect = document.getElementById('modelSelect');
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
const confirmDialog = document.getElementById('confirmDialog');
const dialogTitle = document.getElementById('dialogTitle');
const dialogMessage = document.getElementById('dialogMessage');
const dialogConfirm = document.getElementById('dialogConfirm');
const dialogCancel = document.getElementById('dialogCancel');

// Theme Management
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// Initialize theme
const savedTheme = localStorage.getItem('theme') || 'light';
setTheme(savedTheme);
themeToggle.addEventListener('click', toggleTheme);

// Drag and Drop File Handling
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    uploadArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, unhighlight, false);
});

function highlight() {
    uploadArea.classList.add('highlight');
}

function unhighlight() {
    uploadArea.classList.remove('highlight');
}

// Handle file drop
uploadArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length) {
        fileInput.files = files;
        updateFileName();
    }
}

// Handle file selection
fileInput.addEventListener('change', updateFileName);

function updateFileName() {
    if (fileInput.files.length) {
        const file = fileInput.files[0];
        fileName.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        analyzeBtn.disabled = false;
    } else {
        fileName.textContent = 'No file selected';
        analyzeBtn.disabled = true;
    }
}

// Confirmation Dialog
function showConfirmation(title, message, confirmCallback) {
    dialogTitle.textContent = title;
    dialogMessage.textContent = message;
    confirmDialog.classList.add('active');

    const cleanup = () => {
        dialogConfirm.removeEventListener('click', confirmHandler);
        dialogCancel.removeEventListener('click', cancelHandler);
        confirmDialog.classList.remove('active');
    };

    const confirmHandler = () => {
        cleanup();
        confirmCallback();
    };

    const cancelHandler = () => {
        cleanup();
    };

    dialogConfirm.addEventListener('click', confirmHandler);
    dialogCancel.addEventListener('click', cancelHandler);
}

// Handle analyze button click with confirmation
analyzeBtn.addEventListener('click', () => {
    if (!fileInput.files.length) {
        showStatus('Please select a file first', 'error');
        return;
    }

    showConfirmation(
        'Confirm Analysis',
        'This will process your file and use AI to generate insights. Continue?',
        analyzeFile
    );
});

function analyzeFile() {
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    // Add model selection to form data
    const model = modelSelect.value;
    formData.append('model', model);

    showStatus('<i class="fas fa-spinner fa-spin"></i> Analyzing file and generating AI insights...', 'info');
    analyzeBtn.disabled = true;
    resultsDiv.style.display = 'none';

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Upload failed');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showStatus('<i class="fas fa-check-circle"></i> Analysis complete!', 'success');
        displayResults(data);
    })
    .catch(error => {
        showStatus(`<i class="fas fa-exclamation-circle"></i> Error: ${error.message}`, 'error');
        console.error('Error:', error);
    })
    .finally(() => {
        analyzeBtn.disabled = false;
    });
}

function showStatus(message, type) {
    statusDiv.innerHTML = message;
    statusDiv.className = `status ${type}`;
    statusDiv.style.display = 'flex';
}

function displayResults(data) {
    resultsDiv.style.display = 'block';
    
    // Display stats grid
    const info = data.summary.file_info;
    statsGrid.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${info.rows.toLocaleString()}</div>
            <div class="stat-label">Rows</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${info.columns}</div>
            <div class="stat-label">Columns</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${info.numeric_columns.length}</div>
            <div class="stat-label">Numeric Columns</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${info.column_names.length}</div>
            <div class="stat-label">Total Columns</div>
        </div>
    `;
    
    // Display numeric summary
    if (Object.keys(data.summary.numeric_summary).length > 0) {
        let summaryHTML = `<table><thead><tr><th>Metric</th>`;
        
        // Add column headers
        Object.keys(data.summary.numeric_summary).forEach(col => {
            summaryHTML += `<th>${col}</th>`;
        });
        summaryHTML += `</tr></thead><tbody>`;
        
        // Add rows for each metric
        ['Average', 'Minimum', 'Median', 'Maximum'].forEach(metric => {
            summaryHTML += `<tr><td>${metric}</td>`;
            Object.values(data.summary.numeric_summary).forEach(col => {
                const value = col[metric];
                summaryHTML += `<td>${value === null ? 'N/A' : (typeof value === 'number' ? value.toFixed(2) : value)}</td>`;
            });
            summaryHTML += `</tr>`;
        });
        
        summaryHTML += `</tbody></table>`;
        numericSummary.innerHTML = summaryHTML;
    } else {
        numericSummary.innerHTML = '<p>No numeric columns found in the dataset</p>';
    }
    
    // Display visualizations
    if (Object.keys(data.visualizations).length > 0) {
        let vizHTML = '';
        Object.entries(data.visualizations).forEach(([name, imgData]) => {
            const colName = name.replace('_hist', '');
            vizHTML += `
                <div class="visualization">
                    <div class="visualization-title">Distribution of ${colName}</div>
                    <img src="data:image/png;base64,${imgData}" alt="${colName} histogram">
                </div>
            `;
        });
        visualizationsContent.innerHTML = vizHTML;
    } else {
        visualizationsContent.innerHTML = '<p>No visualizations available (no numeric columns found)</p>';
    }
    
    // Display AI insights
    if (data.ai_insights) {
        if (data.ai_insights.error) {
            aiInsightsContent.innerHTML = `
                <div class="ai-insights">
                    <div class="ai-insights-header">
                        <div class="ai-insights-title">
                            <i class="fas fa-exclamation-triangle"></i> AI Insights Error
                        </div>
                    </div>
                    <div class="ai-insights-content">
                        ${data.ai_insights.error}
                    </div>
                </div>
            `;
        } else if (data.ai_insights.insights) {
            aiInsightsContent.innerHTML = `
                <div class="ai-insights">
                    <div class="ai-insights-header">
                        <div class="ai-insights-title">
                            <i class="fas fa-robot"></i> AI-Powered Insights
                        </div>
                        <div class="ai-insights-model">
                            ${data.ai_insights.model}
                        </div>
                    </div>
                    <div class="ai-insights-content">
                        ${data.ai_insights.insights}
                    </div>
                    <div class="ai-insights-footer">
                        Tokens used: ${data.ai_insights.usage.total_tokens} 
                        (Prompt: ${data.ai_insights.usage.prompt_tokens}, 
                        Completion: ${data.ai_insights.usage.completion_tokens})
                    </div>
                </div>
            `;
        }
    }
}

// Warn before page unload if analysis is in progress
let isProcessing = false;
window.addEventListener('beforeunload', (e) => {
    if (isProcessing) {
        e.preventDefault();
        return e.returnValue = 'Your analysis is in progress. Are you sure you want to leave?';
    }
});
