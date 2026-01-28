// Global state
let currentLogs = null;
let currentTab = 'csv';
let uploadedFile = null;

// History Manager
const HistoryManager = {
    storageKey: 'logParserHistory',
    maxEntries: 50,

    init() {
        try {
            const data = localStorage.getItem(this.storageKey);
            if (!data) {
                this.save({ entries: [], maxEntries: this.maxEntries });
            } else {
                const parsed = JSON.parse(data);
                if (!parsed.entries || !Array.isArray(parsed.entries)) {
                    this.save({ entries: [], maxEntries: this.maxEntries });
                }
            }
        } catch (e) {
            console.error('Failed to initialize history:', e);
            this.save({ entries: [], maxEntries: this.maxEntries });
        }
    },

    save(data) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(data));
        } catch (e) {
            if (e.name === 'QuotaExceededError') {
                console.warn('Storage quota exceeded, pruning entries...');
                this.pruneOldEntries(true);
            } else {
                console.error('Failed to save history:', e);
            }
        }
    },

    load() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : { entries: [], maxEntries: this.maxEntries };
        } catch (e) {
            console.error('Failed to load history:', e);
            return { entries: [], maxEntries: this.maxEntries };
        }
    },

    saveEntry(logs, sourceType, sourceName, config) {
        try {
            // Truncate large log arrays to prevent storage issues
            const truncatedLogs = logs.length > 100 ? logs.slice(0, 100) : logs;

            const entry = {
                id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                timestamp: Date.now(),
                sourceType: sourceType,
                sourceName: sourceName,
                configuration: config,
                entryCount: logs.length,
                logs: truncatedLogs,
                preview: this.generatePreview(logs),
                starred: false
            };

            const data = this.load();
            data.entries.unshift(entry);

            // Auto-prune if needed
            if (data.entries.length > this.maxEntries) {
                this.pruneOldEntries(false, data);
            }

            this.save(data);
            return entry;
        } catch (e) {
            console.error('Failed to save history entry:', e);
            return null;
        }
    },

    getHistory(filterStarred = false) {
        const data = this.load();
        let entries = data.entries || [];

        if (filterStarred) {
            entries = entries.filter(e => e.starred);
        }

        // Sort: starred first, then by timestamp
        entries.sort((a, b) => {
            if (a.starred && !b.starred) return -1;
            if (!a.starred && b.starred) return 1;
            return b.timestamp - a.timestamp;
        });

        return entries;
    },

    getEntry(id) {
        const data = this.load();
        return data.entries.find(e => e.id === id);
    },

    deleteEntry(id) {
        const data = this.load();
        data.entries = data.entries.filter(e => e.id !== id);
        this.save(data);
    },

    clearAll(keepStarred = true) {
        const data = this.load();
        if (keepStarred) {
            data.entries = data.entries.filter(e => e.starred);
        } else {
            data.entries = [];
        }
        this.save(data);
    },

    toggleStar(id) {
        const data = this.load();
        const entry = data.entries.find(e => e.id === id);
        if (entry) {
            entry.starred = !entry.starred;
            this.save(data);
            return entry.starred;
        }
        return false;
    },

    pruneOldEntries(force = false, existingData = null) {
        const data = existingData || this.load();
        const nonStarred = data.entries.filter(e => !e.starred);
        const starred = data.entries.filter(e => e.starred);

        if (force) {
            // Remove half of non-starred entries
            const toKeep = Math.floor(nonStarred.length / 2);
            data.entries = [...starred, ...nonStarred.slice(0, toKeep)];
        } else {
            // Remove oldest non-starred entries to fit limit
            const maxNonStarred = this.maxEntries - starred.length;
            data.entries = [...starred, ...nonStarred.slice(0, maxNonStarred)];
        }

        this.save(data);
    },

    generatePreview(logs) {
        if (!logs || logs.length === 0) return 'No logs';
        const firstLog = JSON.stringify(logs[0]);
        return firstLog.length > 100 ? firstLog.substring(0, 100) + '...' : firstLog;
    },

    checkStorageSize() {
        try {
            const data = localStorage.getItem(this.storageKey);
            if (data) {
                const size = new Blob([data]).size;
                const sizeMB = (size / (1024 * 1024)).toFixed(2);
                console.log(`History storage size: ${sizeMB} MB`);
                return size;
            }
        } catch (e) {
            console.error('Failed to check storage size:', e);
        }
        return 0;
    }
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    HistoryManager.init();
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

        // Escape: Close modal or history sidebar
        if (e.key === 'Escape') {
            const sidebar = document.getElementById('history-sidebar');
            if (sidebar && sidebar.classList.contains('open')) {
                toggleHistory();
            } else {
                closeHelp();
            }
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

            // Save to history
            let sourceName;
            if (currentTab === 'csv') {
                sourceName = uploadedFile ? uploadedFile.name : 'CSV File';
            } else {
                // For text input, show a preview of the content
                const textContent = document.getElementById('text-input').value.trim();
                const firstLine = textContent.split('\n')[0];
                const preview = firstLine.length > 50 ? firstLine.substring(0, 50) + '...' : firstLine;
                sourceName = preview || 'Text Input';
            }
            const config = {
                decode_base64: document.getElementById('decode-base64').checked,
                redact: document.getElementById('redact').checked,
                keep_chars: parseInt(document.getElementById('keep-chars').value),
                include_metadata: currentTab === 'csv' ? document.getElementById('include-metadata').checked : false,
                content_column: currentTab === 'csv' ? document.getElementById('content-column').value : null
            };
            HistoryManager.saveEntry(response.logs, currentTab, sourceName, config);
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
    const placeholder = document.getElementById('right-panel-placeholder');

    let countText = `${count} log${count !== 1 ? 's' : ''} parsed`;
    if (stats) {
        countText += ` | ${stats.total_rows} total rows`;
    }

    resultsCount.textContent = countText;
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');

    // Hide placeholder
    if (placeholder) {
        placeholder.classList.add('hidden');
    }
}

function hideResults() {
    const resultsSection = document.getElementById('results-section');
    const placeholder = document.getElementById('right-panel-placeholder');

    resultsSection.style.display = 'none';

    // Show placeholder
    if (placeholder) {
        placeholder.classList.remove('hidden');
    }
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

// Toggle Options Section
function toggleOptions() {
    const content = document.getElementById('options-content');
    const icon = document.getElementById('options-icon');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.classList.add('expanded');
    } else {
        content.style.display = 'none';
        icon.classList.remove('expanded');
    }
}

// History Functions
let currentHistoryFilter = { starred: false, search: '' };

function toggleHistory(event) {
    // Stop event propagation to prevent window.onclick from interfering
    if (event) {
        event.stopPropagation();
    }

    const sidebar = document.getElementById('history-sidebar');
    if (!sidebar) {
        console.error('History sidebar element not found!');
        return;
    }

    const isOpen = sidebar.classList.contains('open');

    if (isOpen) {
        sidebar.classList.remove('open');
    } else {
        sidebar.classList.add('open');
        renderHistoryList();
    }
}

function renderHistoryList(searchTerm = '', starredOnly = false) {
    const entries = HistoryManager.getHistory(starredOnly);
    const listContainer = document.getElementById('history-list');
    const emptyState = document.getElementById('history-empty');

    // Filter by search term
    let filteredEntries = entries;
    if (searchTerm) {
        const search = searchTerm.toLowerCase();
        filteredEntries = entries.filter(e =>
            e.sourceName.toLowerCase().includes(search) ||
            e.preview.toLowerCase().includes(search) ||
            e.sourceType.toLowerCase().includes(search)
        );
    }

    if (filteredEntries.length === 0) {
        listContainer.style.display = 'none';
        emptyState.style.display = 'flex';
        return;
    }

    listContainer.style.display = 'block';
    emptyState.style.display = 'none';

    listContainer.innerHTML = filteredEntries.map((entry, index) => `
        <div class="history-entry ${entry.starred ? 'starred' : ''}" data-id="${entry.id}">
            <div class="history-entry-number">#${index + 1}</div>
            <div class="history-entry-content">
                <div class="history-entry-header">
                    <div class="history-header-left">
                        <span class="history-source-name">${entry.sourceName}</span>
                        <span class="source-type-badge ${entry.sourceType}">${entry.sourceType === 'csv' ? '📁 CSV' : '📄 Text'}</span>
                    </div>
                    <button class="star-button" onclick="toggleStarEntry('${entry.id}')" title="${entry.starred ? 'Unstar' : 'Star'}">
                        ${entry.starred ? '★' : '☆'}
                    </button>
                </div>
                <div class="history-entry-meta">
                    <span class="history-entry-count">📊 ${entry.entryCount} log${entry.entryCount !== 1 ? 's' : ''}</span>
                    <span class="history-timestamp">🕒 ${formatTimeAgo(entry.timestamp)}</span>
                </div>
                <div class="history-entry-actions">
                    <button class="btn-secondary btn-sm" onclick="restoreHistory('${entry.id}')">View</button>
                    <button class="btn-secondary btn-sm btn-delete" onclick="deleteHistoryEntry('${entry.id}')">Delete</button>
                </div>
            </div>
        </div>
    `).join('');
}

function restoreHistory(id) {
    const entry = HistoryManager.getEntry(id);
    if (!entry) {
        showError('History entry not found');
        return;
    }

    // Restore logs
    currentLogs = entry.logs;
    displayResults(currentLogs, 'pretty');

    // Update results section
    showResults(entry.entryCount, null);

    // Close sidebar
    toggleHistory();

    // Scroll to results (scroll to top of right panel)
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function deleteHistoryEntry(id) {
    const entry = HistoryManager.getEntry(id);
    if (!entry) return;

    const confirmMsg = entry.starred
        ? 'This is a starred entry. Are you sure you want to delete it?'
        : 'Are you sure you want to delete this entry?';

    if (confirm(confirmMsg)) {
        HistoryManager.deleteEntry(id);
        renderHistoryList(currentHistoryFilter.search, currentHistoryFilter.starred);
    }
}

function clearHistory() {
    const data = HistoryManager.load();
    const starredCount = data.entries.filter(e => e.starred).length;
    const totalCount = data.entries.length;

    if (totalCount === 0) {
        alert('History is already empty');
        return;
    }

    let confirmMsg = 'Clear all history?';
    let keepStarred = true;

    if (starredCount > 0) {
        const choice = confirm(`Clear all ${totalCount} entries?\n\nClick OK to keep ${starredCount} starred entries, or Cancel to delete everything.`);
        if (choice) {
            keepStarred = true;
        } else {
            const confirmAll = confirm('Delete ALL entries including starred ones?');
            if (!confirmAll) return;
            keepStarred = false;
        }
    } else {
        if (!confirm(`Delete all ${totalCount} entries?`)) return;
        keepStarred = false;
    }

    HistoryManager.clearAll(keepStarred);
    renderHistoryList(currentHistoryFilter.search, currentHistoryFilter.starred);
}

function toggleStarEntry(id) {
    const newState = HistoryManager.toggleStar(id);
    renderHistoryList(currentHistoryFilter.search, currentHistoryFilter.starred);
}

function filterStarred(enabled) {
    currentHistoryFilter.starred = enabled;

    // Update button states
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(btn => {
        if (enabled && btn.dataset.filter === 'starred') {
            btn.classList.add('active');
        } else if (!enabled && btn.dataset.filter === 'all') {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    renderHistoryList(currentHistoryFilter.search, enabled);
}

function formatTimeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

    const date = new Date(timestamp);
    return date.toLocaleDateString();
}

function searchHistory() {
    const searchTerm = document.getElementById('history-search').value;
    currentHistoryFilter.search = searchTerm;
    renderHistoryList(searchTerm, currentHistoryFilter.starred);
}

// Click outside modal to close
window.onclick = function(event) {
    const modal = document.getElementById('help-modal');
    if (event.target === modal) {
        closeHelp();
    }

    // Close history sidebar when clicking outside
    const sidebar = document.getElementById('history-sidebar');
    if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(event.target)) {
        // Check if click was on history button (check both the button element and its onclick attribute)
        const historyBtn = event.target.closest('.btn-with-text') || event.target.closest('[onclick*="toggleHistory"]');
        if (!historyBtn) {
            toggleHistory();
        }
    }
}

// Add syntax highlighting CSS (CloudBees dark theme colors)
const style = document.createElement('style');
style.textContent = `
    #results-output .key { color: #3b9aee; }
    #results-output .string { color: #98c379; }
    #results-output .number { color: #d19a66; }
    #results-output .boolean { color: #c678dd; }
    #results-output .null { color: #82868b; }
`;
document.head.appendChild(style);
