#!/usr/bin/env python3
"""
Flask Web UI for Log Parser Utility

A lightweight web interface for parsing logs from Datadog and CSV files.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Add parent directory to path to import parser modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datadog_parser_v2 import parse_datadog_logs
from csv_log_extractor import extract_logs_from_csv, count_logs_in_csv

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'txt', 'log', 'json'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/api/parse-text', methods=['POST'])
def parse_text():
    """
    Parse text logs (Datadog Protocol Buffer format)

    POST body:
    {
        "text": "log content",
        "decode_base64": true,
        "redact": false,
        "keep_chars": 4
    }
    """
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data['text']
        decode_base64 = data.get('decode_base64', True)
        redact = data.get('redact', False)
        keep_chars = int(data.get('keep_chars', 4))

        # Parse logs
        logs = parse_datadog_logs(
            text,
            decode_base64=decode_base64,
            redact=redact,
            keep_chars=keep_chars
        )

        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/parse-csv', methods=['POST'])
def parse_csv():
    """
    Parse CSV file

    Form data:
    - file: CSV file
    - content_column: Column name (default: Content)
    - include_metadata: true/false
    - decode_base64: true/false
    - redact: true/false
    - keep_chars: number
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use .csv, .txt, .log, or .json'}), 400

        # Get options
        content_column = request.form.get('content_column', 'Content')
        include_metadata = request.form.get('include_metadata', 'true').lower() == 'true'
        decode_base64 = request.form.get('decode_base64', 'true').lower() == 'true'
        redact = request.form.get('redact', 'false').lower() == 'true'
        keep_chars = int(request.form.get('keep_chars', 4))

        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # First, count logs
            stats = count_logs_in_csv(filepath, content_column)

            # Then extract logs
            logs = extract_logs_from_csv(
                filepath,
                content_column=content_column,
                include_metadata=include_metadata,
                decode_base64=decode_base64,
                redact=redact,
                keep_chars=keep_chars
            )

            return jsonify({
                'success': True,
                'count': len(logs),
                'stats': stats,
                'logs': logs
            })

        finally:
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/download', methods=['POST'])
def download():
    """
    Download parsed logs as JSON file

    POST body:
    {
        "logs": [...],
        "format": "pretty" | "compact" | "array",
        "filename": "logs.json"
    }
    """
    try:
        data = request.get_json()

        if not data or 'logs' not in data:
            return jsonify({'error': 'No logs provided'}), 400

        logs = data['logs']
        format_type = data.get('format', 'pretty')
        filename = data.get('filename', 'parsed_logs.json')

        # Format JSON based on type
        if format_type == 'compact':
            json_content = json.dumps(logs, ensure_ascii=False, sort_keys=True)
        elif format_type == 'array':
            json_content = json.dumps(logs, indent=2, ensure_ascii=False, sort_keys=True)
        else:  # pretty (default)
            json_content = json.dumps(logs, indent=2, ensure_ascii=False, sort_keys=True)

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.write(json_content)
        temp_file.close()

        # Send file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large. Maximum size is 50MB.'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Log Parser Utility - Web UI")
    print("=" * 60)
    print(f"   Server: http://localhost:5000")
    print(f"   Max file size: 50MB")
    print("=" * 60)
    print("\n📝 Press Ctrl+C to stop the server\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
