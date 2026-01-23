// Global state
let currentLogs = null;
let currentTab = 'csv';
let uploadedFile = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeDragAndDrop();
    initializeKeyboardShortcuts();
});

// Initialize Event Listeners
function initializeEventListeners() {
    // File input change
    document.getElementById('file-input').addEventListener('change', handleFileSelect);

    // Keep chars slider
    const keepCharsSlider = document.getElementById('keep-chars');
    const keepCharsValue = document.getElementById('keep-chars-value');
    keepCharsSlider.addEventListener('input', function() {
        keepCharsValue.textContent = this.value;
    });

    // Format select change
    document.getElementById('format-select').addEventListener('change', function() {
        if (currentLogs) {
            displayResults(currentLogs, this.value);
        }
    });

    // Redact checkbox - enable/disable keep-chars slider
    document.getElementById('redact').addEventListener('change', function() {
        document.getElementById('keep-chars').disabled = !this.checked;
    });
}

// Initialize Drag and Drop
function initializeDragAndDrop() {
    const uploadArea = document.getElementById('upload-area');

    uploadArea.addEventListener('click', function() {
        document.getElementById('file-input').click();
    });

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// Initialize Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter: Parse logs
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            parseLog();
        }

        // Ctrl/Cmd + C when results are visible: Copy results
        if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
            const resultsSection = document.getElementById('results-section');
            if (resultsSection.style.display !== 'none') {
                copyResults();
            }
        }

        // Escape: Close modal
        if (e.key === 'Escape') {
            closeHelp();
        }
    });
}

// Tab Switching
function switchTab(tab) {
    currentTab = tab;

    // Update tab buttons
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    document.getElementById('csv-tab').classList.toggle('active', tab === 'csv');
    document.getElementById('text-tab').classList.toggle('active', tab === 'text');
}

// Handle File Selection
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    uploadedFile = file;

    // Update upload area to show file info
    const uploadArea = document.getElementById('upload-area');
    uploadArea.innerHTML = `
        <div class="upload-icon">📄</div>
        <p class="upload-text"><strong>${file.name}</strong></p>
        <p class="upload-hint">${formatFileSize(file.size)} | <span class="link" onclick="clearFile()">Remove</span></p>
    `;
}

function clearFile() {
    uploadedFile = null;
    document.getElementById('file-input').value = '';

    // Reset upload area
    const uploadArea = document.getElementById('upload-area');
    uploadArea.innerHTML = `
        <div class="upload-icon">📁</div>
        <p class="upload-text">Drop CSV file here or <span class="link" onclick="document.getElementById('file-input').click()">browse</span></p>
        <p class="upload-hint">Supports .csv, .txt, .log files (max 50MB)</p>
    `;
}

// Format File Size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Parse Logs
async function parseLog() {
    hideError();
    hideResults();

    // Validate input
    if (currentTab === 'csv' && !uploadedFile) {
        showError('Please select a CSV file to parse');
        return;
    }

    if (currentTab === 'text') {
        const text = document.getElementById('text-input').value.trim();
        if (!text) {
            showError('Please enter text to parse');
            return;
        }
    }

    // Show progress
    showProgress();

    // Disable parse button
    const parseBtn = document.getElementById('parse-btn');
    parseBtn.disabled = true;
    parseBtn.textContent = '⏳ Parsing...';

    try {
        let response;

        if (currentTab === 'csv') {
            response = await parseCSV();
        } else {
            response = await parseText();
        }

        if (response.success) {
            currentLogs = response.logs;
            displayResults(currentLogs, 'pretty');
            showResults(response.count, response.stats);
        } else {
            showError(response.error || 'Failed to parse logs');
        }
    } catch (error) {
        console.error('Parse error:', error);
        showError(error.message || 'An unexpected error occurred');
    } finally {
        hideProgress();
        parseBtn.disabled = false;
        parseBtn.textContent = '🚀 Parse Logs';
    }
}

// Parse CSV
async function parseCSV() {
    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('content_column', document.getElementById('content-column').value);
    formData.append('include_metadata', document.getElementById('include-metadata').checked);
    formData.append('decode_base64', document.getElementById('decode-base64').checked);
    formData.append('redact', document.getElementById('redact').checked);
    formData.append('keep_chars', document.getElementById('keep-chars').value);

    const response = await fetch('/api/parse-csv', {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

// Parse Text
async function parseText() {
    const text = document.getElementById('text-input').value;

    const response = await fetch('/api/parse-text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: text,
            decode_base64: document.getElementById('decode-base64').checked,
            redact: document.getElementById('redact').checked,
            keep_chars: parseInt(document.getElementById('keep-chars').value)
        })
    });

    return await response.json();
}

// Display Results
function displayResults(logs, format) {
    const output = document.getElementById('results-output');
    let content;

    switch (format) {
        case 'compact':
            content = logs.map(log => JSON.stringify(log)).join('\n');
            break;
        case 'array':
            content = JSON.stringify(logs, null, 2);
            break;
        default: // pretty
            content = logs.map(log => JSON.stringify(log, null, 2)).join('\n\n');
    }

    output.textContent = content;

    // Syntax highlighting (simple)
    output.innerHTML = syntaxHighlight(content);
}

// Simple Syntax Highlighting
function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        let cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

// Show Results
function showResults(count, stats) {
    const resultsSection = document.getElementById('results-section');
    const resultsCount = document.getElementById('results-count');

    let countText = `${count} log${count !== 1 ? 's' : ''} parsed`;
    if (stats) {
        countText += ` | ${stats.total_rows} total rows`;
    }

    resultsCount.textContent = countText;
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
}

function hideResults() {
    document.getElementById('results-section').style.display = 'none';
}

// Download Results
async function downloadResults() {
    if (!currentLogs) return;

    const format = document.getElementById('format-select').value;
    const filename = `parsed_logs_${new Date().getTime()}.json`;

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                logs: currentLogs,
                format: format,
                filename: filename
            })
        });

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
        showError('Failed to download results: ' + error.message);
    }
}

// Copy Results
function copyResults() {
    const output = document.getElementById('results-output');
    const text = output.textContent;

    navigator.clipboard.writeText(text).then(() => {
        // Show brief success message
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        showError('Failed to copy: ' + err.message);
    });
}

// Error Handling
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorText = document.getElementById('error-text');

    errorText.textContent = message;
    errorSection.style.display = 'block';
    errorSection.classList.add('fade-in');

    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
    document.getElementById('error-section').style.display = 'none';
}

function closeError() {
    hideError();
}

// Progress Bar
function showProgress() {
    document.getElementById('progress-bar').style.display = 'block';
}

function hideProgress() {
    document.getElementById('progress-bar').style.display = 'none';
}

// Help Modal
function showHelp() {
    document.getElementById('help-modal').style.display = 'flex';
}

function closeHelp() {
    document.getElementById('help-modal').style.display = 'none';
}

// Settings Modal (placeholder)
function toggleSettings() {
    alert('Settings panel coming soon!');
}

// Click outside modal to close
window.onclick = function(event) {
    const modal = document.getElementById('help-modal');
    if (event.target === modal) {
        closeHelp();
    }
}

// Add syntax highlighting CSS
const style = document.createElement('style');
style.textContent = `
    #results-output .key { color: #881391; }
    #results-output .string { color: #1a7f1a; }
    #results-output .number { color: #1c00cf; }
    #results-output .boolean { color: #0c4f7c; }
    #results-output .null { color: #808080; }
`;
document.head.appendChild(style);
