# Log Parser Utility - Web UI

Modern web interface for parsing logs from Datadog, CSV files, and more.

## 🎨 Features

- 📁 **Drag-and-drop file upload** for CSV files
- 📄 **Text input** for pasting logs directly
- 🔒 **Smart redaction** of sensitive fields
- ⚙️ **Configurable options** (base64 decoding, metadata, etc.)
- 📊 **Live results preview** with syntax highlighting
- ⬇️ **Download results** in multiple formats
- 📋 **Copy to clipboard** functionality
- 🎯 **Responsive design** works on desktop and mobile
- ⌨️ **Keyboard shortcuts** for power users

## 🚀 Quick Start

### Installation

```bash
# Navigate to web directory
cd datadog-log-parser/src/web

# Install dependencies
pip install -r requirements.txt

# Or use pip3
pip3 install -r requirements.txt
```

### Run the Server

```bash
# Start the web server
python app.py

# Or use python3
python3 app.py
```

The server will start on `http://localhost:5000`

Open your browser and navigate to: **http://localhost:5000**

## 📖 Usage

### Parsing CSV Files

1. Click the **"📁 CSV File"** tab
2. Drag and drop your CSV file or click to browse
3. (Optional) Change the content column name if different from "Content"
4. Configure options (redaction, base64 decoding, etc.)
5. Click **"🚀 Parse Logs"**
6. View results and download if needed

### Parsing Text Logs

1. Click the **"📄 Text/Paste"** tab
2. Paste your log content (Datadog Protocol Buffer format)
3. Configure options as needed
4. Click **"🚀 Parse Logs"**
5. View and download results

## ⚙️ Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| **Decode Base64** | Decode base64 encoded fields (keys, certificates) | ✅ Enabled |
| **Redact Sensitive Fields** | Hide sensitive data (keys, tokens, secrets) | ❌ Disabled |
| **Include Metadata** | Include CSV metadata (Date, Host, Service) | ✅ Enabled |
| **Keep Characters** | Number of chars to keep when redacting | 4 |

## 🎯 Output Formats

- **Pretty JSON** - Formatted with indentation (default)
- **Compact JSON** - Single line per entry
- **JSON Array** - All entries in one array

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + Enter` | Parse logs |
| `Ctrl/Cmd + C` | Copy results (when results visible) |
| `Esc` | Close help modal |

## 🛠️ API Endpoints

The web UI exposes these REST API endpoints:

### Parse Text Logs

```http
POST /api/parse-text
Content-Type: application/json

{
  "text": "Received event id:\"123\" ...",
  "decode_base64": true,
  "redact": false,
  "keep_chars": 4
}
```

### Parse CSV File

```http
POST /api/parse-csv
Content-Type: multipart/form-data

file: <file>
content_column: Content
include_metadata: true
decode_base64: true
redact: false
keep_chars: 4
```

### Download Results

```http
POST /api/download
Content-Type: application/json

{
  "logs": [...],
  "format": "pretty" | "compact" | "array",
  "filename": "logs.json"
}
```

### Health Check

```http
GET /api/health
```

## 🔧 Development

### Project Structure

```
src/web/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── static/
│   ├── style.css      # Styling
│   └── app.js         # Frontend logic
└── templates/
    └── index.html     # Main UI
```

### Running in Development Mode

```bash
# Development mode (auto-reload enabled)
python app.py
```

Flask will run in debug mode with auto-reload enabled.

### Running in Production

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🌐 Deployment

### Deploy to Cloud

The web UI can be deployed to various cloud platforms:

**Heroku:**
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
git push heroku main
```

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```

**AWS/GCP/Azure:**
Use their respective Python web app services.

## 🔒 Security Considerations

- File uploads are limited to 50MB
- Only allowed file extensions: `.csv`, `.txt`, `.log`, `.json`
- Temporary files are cleaned up after processing
- Redaction feature helps protect sensitive data

## 🐛 Troubleshooting

### Port Already in Use

If port 5000 is already in use, change it in `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Use port 8080
```

### Import Errors

Make sure you're running from the correct directory:

```bash
cd datadog-log-parser/src/web
python app.py
```

### File Upload Fails

Check that the file size is under 50MB and has an allowed extension.

## 📊 Performance

- Handles CSV files up to 50MB
- Parses ~1000 logs per second
- Responsive UI with progress indicators
- Automatic cleanup of temporary files

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Add batch processing for multiple files
- Add log filtering and search
- Add export to other formats (XML, YAML)
- Add user authentication for shared deployments
- Add real-time log streaming

## 📄 License

Same as parent project - Free to use and modify.

## 🆘 Support

For issues or questions:
1. Check the main [project documentation](../../docs/)
2. Review [examples](../../examples/)
3. Check browser console for JavaScript errors

---

**Made with ❤️ for easier log parsing**
