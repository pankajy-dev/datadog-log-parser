# Datadog Log Parser

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Standalone](https://img.shields.io/badge/standalone-no%20server%20needed-green.svg)](standalone/)

A comprehensive utility for parsing and extracting logs from Datadog format, CSV exports, and other log sources with support for Protocol Buffer text format, redaction, and multiple output formats.

## 🚀 Quick Start (Standalone Version - Recommended)

### **No Server, No Installation Required!**

**👉 [Open Log Parser](standalone/log-parser.html) 👈**

Or from command line:
```bash
open standalone/log-parser.html
```

Then **bookmark it** in your browser for instant access!

**Features:**
- ✅ Parse Datadog Protocol Buffer logs
- ✅ Extract logs from CSV files
- ✅ Decode Base64 fields
- ✅ Redact sensitive data
- ✅ Local history with starring
- ✅ 100% client-side (no data sent anywhere)
- ✅ Works offline
- ✅ Modern dark UI theme
- ✅ Defaults to Text/Paste tab for quick access

👉 **See [standalone/README.md](standalone/README.md) for full documentation**

---

## 🐍 Python CLI Tools (Optional)

If you prefer command-line tools or need to integrate into scripts:

### Installation

```bash
# No dependencies needed! Pure Python.
# (Optional) Only if you want the Flask web UI:
pip install flask
```

### Command Line Usage

```bash
# Extract logs from CSV file
python3 src/csv_log_extractor.py -f your-logs.csv --redact

# Parse logs from text/string
python3 src/parse_datadog_logs.py "Received event id:..."

# Save to separate JSON files
python3 src/csv_log_extractor.py -f logs.csv --redact -o output/
```

### Python Library Usage

```python
from src.datadog_parser_v2 import parse_datadog_logs

# Parse logs
logs = parse_datadog_logs(
    log_text,
    decode_base64=True,
    redact=True,
    keep_chars=4
)

# Access parsed data
for log in logs:
    print(log)
```

---

## 🌐 Web UI (Flask Server - Optional)

If you want to run the web interface as a local server:

### Installation
```bash
pip install flask
```

### Run Server
```bash
python3 -m flask --app src/web/app run --port 5000
# Open browser: http://localhost:5000
```

**Note:** The standalone version (above) is recommended as it requires no server setup.

---

## 📦 Project Structure

```
datadog-log-parser/
├── standalone/                    # 🌟 Standalone HTML version (RECOMMENDED)
│   ├── log-parser.html           # Single-file app, just open it!
│   └── README.md                 # Standalone docs
│
├── src/                          # Python source code (optional)
│   ├── datadog_parser_v2.py     # Core parser library
│   ├── csv_log_extractor.py     # CLI for CSV files
│   ├── parse_datadog_logs.py    # CLI for text/string logs
│   └── web/                      # Flask web UI (optional)
│       ├── app.py                # Flask application
│       ├── templates/            # HTML templates
│       └── static/               # CSS, JS, assets
│
├── tests/                        # Test files
└── README.md                     # This file
```

---

## 🎯 Use Cases

### Standalone Version (Recommended for most users)
- ✅ Quick log parsing without setup
- ✅ Personal use, local files
- ✅ Bookmark and access anytime
- ✅ Maximum privacy (100% local)

### Python CLI Tools
- ✅ Batch processing large files
- ✅ Integration into shell scripts
- ✅ Automation and CI/CD pipelines
- ✅ Programmatic access via Python library

### Flask Web UI
- ✅ Team use on local network
- ✅ Consistent URL for multiple users
- ✅ When you prefer server-based architecture

---

## ✨ Features

### Parsing Capabilities
- **Datadog Protocol Buffer format** - Parse native Datadog log format
- **CSV file extraction** - Extract logs from CSV exports
- **JSON support** - Parse JSON logs directly
- **Base64 decoding** - Automatically decode encoded fields
- **Smart redaction** - Hide sensitive data (keys, tokens, passwords)
- **Multiple output formats** - Pretty, compact, or array JSON

### UI Features
- **Modern dark theme** - CloudBees.io inspired design
- **History with starring** - Track and restore previous parses
- **Search and filter** - Find logs quickly
- **Two-column layout** - Input on left, results on right
- **Collapsible options** - Clean, focused interface
- **Keyboard shortcuts** - Efficient workflow

---

## 🔒 Privacy

### Standalone Version
- **100% client-side** - All processing in your browser
- **No data transmission** - Nothing sent to any server
- **LocalStorage only** - History saved locally
- **No tracking** - No analytics, no cookies

### Python CLI Tools
- **Local processing only** - All data stays on your machine
- **No network calls** - Completely offline

---

## 📖 Documentation

- **Standalone Version:** [standalone/README.md](standalone/README.md)
- **Python CLI Tools:** See command help with `--help` flag
- **Web UI:** Access help via ❓ button in the interface
- **Makefile Commands:** Run `make help` to see all available commands

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🌟 Quick Comparison

| Feature | Standalone HTML | Python CLI | Flask Web UI |
|---------|-----------------|------------|--------------|
| **Setup Required** | None | pip install | pip install + run server |
| **Start Command** | Double-click file | `python3 src/...` | `flask run` |
| **Access Method** | file:// or bookmark | Terminal | http://localhost:5000 |
| **Best For** | Personal use, quick access | Scripting, automation | Team use, shared server |
| **Privacy** | 100% local | 100% local | Local server |
| **Portability** | Copy 1 file | Copy project + Python | Copy project + Python |

**👍 Recommended:** Start with the **standalone version** for the easiest experience!

---

**Happy Log Parsing! 🚀**
