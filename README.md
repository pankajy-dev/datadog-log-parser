# Datadog Log Parser

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A comprehensive utility for parsing and extracting logs from Datadog format, CSV exports, and other log sources with support for Protocol Buffer text format, redaction, and multiple output formats.

## 🚀 Quick Start

### Web UI (Recommended for Beginners)

```bash
# Start the web interface
./start-web-ui.sh

# Or manually:
cd src/web
pip3 install -r requirements.txt
python3 app.py

# Open browser: http://localhost:5000
```

### Command Line

```bash
# Extract logs from CSV file
python3 src/csv_log_extractor.py -f your-logs.csv --redact

# Parse logs from text/string
python3 src/parse_datadog_logs.py "Received event id:..."

# Save to separate JSON files
python3 src/csv_log_extractor.py -f logs.csv --redact -o output/
```

## 📦 Project Structure

```
datadog-log-parser/
├── src/                          # Source code
│   ├── parse_datadog_logs.py     # CLI for text/string logs
│   ├── csv_log_extractor.py      # CLI for CSV files
│   ├── datadog_parser_v2.py      # Core parser library
│   └── datadog_log_parser.py     # Alternative implementation
├── tests/                        # Test files
└── README.md                     # This file
```

## 🎯 Features

### Core Features
- ✅ **Protocol Buffer text format** parsing (Datadog style)
- ✅ **JSON format** auto-detection and parsing
- ✅ **CSV extraction** with metadata preservation
- ✅ **Base64 decoding** (public keys, certificates)
- ✅ **Smart redaction** of sensitive data
- ✅ **Multiple output formats** (pretty, compact, array)
- ✅ **Boolean, string, number** value support
- ✅ **Zero dependencies** (pure Python 3)

### Security Features
- 🔒 Automatic detection of sensitive fields
- 🔒 Configurable redaction (keeps first/last N chars)
- 🔒 Clear marking of redacted fields
- 🔒 Safe for sharing in public channels

## 🛠️ Tools

### 1. Web UI (NEW! 🎨)
Modern web interface for easy log parsing - no command line needed!

```bash
./start-web-ui.sh
# Opens http://localhost:5000
```

**Features:**
- 📁 Drag-and-drop file upload
- 📄 Paste text directly
- ⚙️ Visual configuration options
- 📊 Live results with syntax highlighting
- ⬇️ Download in multiple formats
- 🎯 Responsive design

📖 [Web UI Documentation](src/web/README.md)

---

### 2. CSV Log Extractor
Extract and parse logs from CSV exports (Datadog, CloudWatch, etc.)

```bash
python3 src/csv_log_extractor.py -f logs.csv --redact
```

**Use when:**
- You exported logs from Datadog as CSV
- You have logs in CSV format with a content column
- You want to include metadata (Date, Host, Service)

---

### 3. Datadog Log Parser
Parse Protocol Buffer text format logs from strings, files, or stdin.

```bash
python3 src/parse_datadog_logs.py -f logs.txt --redact
```

**Use when:**
- You have raw log text (copy-pasted from Datadog)
- You have a text file with Datadog logs
- You're piping logs from another command

---

### 4. Core Parser Library
Python library for programmatic use in your scripts.

```python
import sys
sys.path.append('src')
from datadog_parser_v2 import parse_datadog_logs

logs = parse_datadog_logs(log_text, redact=True)
```

---

## 📋 Installation

No external dependencies required!

```bash
# Clone or download the utility
cd datadog-log-parser

# Make scripts executable
chmod +x src/*.py

# Run directly
python3 src/csv_log_extractor.py --help
```

### Optional: Add to PATH

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/datadog-log-parser/src"

# Now you can run from anywhere
csv_log_extractor.py -f logs.csv
parse_datadog_logs.py -f logs.txt
```

## 🔒 Redaction Feature

All tools support smart redaction of sensitive fields:

**Redacted field patterns:**
- `public_key`, `private_key`
- `secret`, `token`, `api_key`
- `password`, `credential`
- `auth`, `authorization`

**Example:**
```bash
# Input
"api_key": "abcd1234567890efghijklmnopqrstuvwxyz"

# Output (--redact)
"api_key": "abcd...wxyz"
"api_key_redacted": true
```

Customize the number of characters kept:
```bash
python3 src/csv_log_extractor.py -f logs.csv --redact --keep-chars 6
# Result: "abcd12...uvwxyz"
```

## 📚 Documentation

All documentation is contained in this README file.

## 💡 Common Use Cases

### Use Case 1: Datadog CSV Export with Redaction
```bash
# Extract all logs, redact secrets, save to files
python3 src/csv_log_extractor.py \
  -f datadog-export.csv \
  --redact \
  -o parsed_logs/
```

### Use Case 2: Parse and Filter Logs
```bash
# Extract logs and filter with jq
python3 src/csv_log_extractor.py -f logs.csv --single-json | \
  jq '.[] | select(.log.type == "error")'
```

### Use Case 3: Convert CSV to JSONL
```bash
# Convert to JSON Lines format
python3 src/csv_log_extractor.py \
  -f logs.csv \
  --no-metadata \
  --compact > logs.jsonl
```

### Use Case 4: Python Script Integration
```python
import sys
sys.path.append('src')
from csv_log_extractor import extract_logs_from_csv

# Extract with redaction
logs = extract_logs_from_csv(
    'logs.csv',
    redact=True,
    keep_chars=4
)

# Process
for entry in logs:
    if entry['log'].get('type') == 'error':
        send_alert(entry)
```

## 🌍 Multi-Language Support (Planned)

Future versions will include:
- Go implementation for high-performance parsing
- Node.js library for JavaScript/TypeScript projects
- Rust CLI for ultra-fast processing
- Docker images for containerized environments

## 📊 Performance

- **Fast**: Parses 1000+ logs in seconds
- **Memory efficient**: Streams CSV row by row
- **Large files**: Tested with 10,000+ row CSVs
- **No bloat**: Zero external dependencies

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional log format parsers
- More language implementations
- Custom redaction patterns
- Output format plugins
- Test coverage

## 📝 Version History

### v1.0.0 (2026-01-23)
- Initial release
- Python implementation
- CSV extractor
- Datadog log parser
- Redaction support
- Base64 decoding
- Boolean value support

## 📄 License

Free to use and modify.

---

**Made with ❤️ for better log parsing**
