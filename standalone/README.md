# Log Parser Utility - Standalone Version

## 🚀 No Server Required!

This is a completely client-side version of the Log Parser Utility. Everything runs in your browser - **no Python, no Flask, no server needed!**

## ✨ Features

- ✅ **Parse Datadog Protocol Buffer logs** - Convert to clean JSON
- ✅ **Extract logs from CSV files** - Process large CSV exports
- ✅ **Decode Base64 fields** - Automatically decode encoded data
- ✅ **Redact sensitive data** - Hide keys, tokens, passwords
- ✅ **Local history with starring** - Track and restore previous parses
- ✅ **Modern dark theme** - CloudBees.io inspired design
- ✅ **100% private** - All data stays in your browser
- ✅ **Bookmarkable** - Just open and use

## 📖 How to Use

### Method 1: Open Directly (Recommended)
1. Double-click `log-parser.html`
2. It opens in your browser
3. Bookmark it for easy access!

### Method 2: Use from File System
```bash
open log-parser.html
# or
file:///path/to/log-parser.html
```

### Method 3: Serve Locally (Optional)
```bash
# Python 3
python3 -m http.server 8000

# Then open: http://localhost:8000/log-parser.html
```

## 🎯 Quick Start

1. **CSV Mode**:
   - Drop a CSV file or click to browse
   - Set the content column name (default: "Content")
   - Click "Parse Logs"

2. **Text Mode**:
   - Switch to "Text/Paste" tab
   - Paste Datadog logs directly
   - Click "Parse Logs"

3. **History**:
   - Click "📜 History" button to see past parses
   - Star important entries to protect from auto-deletion
   - Click "View" to restore any previous parse

## ⌨️ Keyboard Shortcuts

- `Ctrl/Cmd + Enter` - Parse logs
- `Ctrl/Cmd + C` - Copy results (when viewing results)
- `Esc` - Close panels

## 🔒 Privacy

- **100% client-side** - No data sent to any server
- **LocalStorage only** - History stored in your browser
- **No tracking** - No analytics, no cookies
- **Offline capable** - Works without internet

## 📦 Single File

The entire application is contained in one HTML file (`log-parser.html`):
- All CSS embedded
- All JavaScript embedded
- No external dependencies
- No build process needed

## 🌟 Advantages Over Server Version

| Feature | Standalone | Server Version |
|---------|-----------|----------------|
| **Setup** | Just open file | Install Python, Flask, dependencies |
| **Start** | Double-click | Run `python app.py` in terminal |
| **Access** | `file://` or bookmark | `http://localhost:5000` |
| **Privacy** | 100% local | Data sent to local server |
| **Portable** | Copy one file | Copy entire project |
| **Updates** | Replace one file | Git pull + restart server |

## 🛠️ Technical Details

### Parsing Logic
- **Protobuf Text Format** - State machine parser for Datadog format
- **CSV Parsing** - Custom parser with quote handling
- **Base64 Decoding** - Built-in `atob()` function
- **JSON Handling** - Native JSON parsing

### Storage
- **LocalStorage** - Max 50 entries (configurable)
- **Auto-pruning** - Removes oldest non-starred entries
- **Starred protection** - Starred entries never auto-deleted

### Browser Compatibility
- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile: ✅ Responsive design

## 📝 Example Usage

### Parse Datadog Logs
```
Received OcPreRegisterControllerMetadataType event id:"3a92e52d"
subject:"http://example.com/cjoc/" type:"cloudbees.platform.jenkins"
data:{provider_info:{provider:"OC"} metadata:{reconcile_type:"controller"}}
```

### Parse CSV
Upload a CSV with columns: Date, Host, Service, Content
- Content column contains the logs to parse
- Other columns included as metadata (optional)

## 🎨 Theme

Uses CloudBees.io inspired dark theme:
- Dark backgrounds: `#2b2d31`, `#1e1f22`
- Blue accents: `#3b9aee`
- Clean, professional interface

## 📄 License

MIT License - Same as the server version

## 🤝 Credits

Converted from the Python/Flask version to pure JavaScript for maximum portability and ease of use.

---

**Tip**: Bookmark `file:///path/to/log-parser.html` in your browser for instant access anytime!
