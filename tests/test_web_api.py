"""
Unit tests for Web UI API endpoints
"""

import pytest
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "web"))

from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    return flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health endpoint returns success"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestParseTextEndpoint:
    """Test text log parsing endpoint"""

    def test_parse_simple_text(self, client):
        """Test parsing simple text log"""
        response = client.post(
            '/api/parse-text',
            json={
                'text': 'message:"hello world"',
                'decode_base64': False,
                'redact': False
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['results']) == 1
        assert data['results'][0]['message'] == 'hello world'

    def test_parse_with_redaction(self, client):
        """Test parsing with redaction enabled"""
        response = client.post(
            '/api/parse-text',
            json={
                'text': 'api_key:"secret123456789"',
                'decode_base64': False,
                'redact': True,
                'keep_chars': 4
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['results'][0]['api_key']['_redacted'] is True

    def test_parse_missing_text(self, client):
        """Test parsing without text parameter"""
        response = client.post(
            '/api/parse-text',
            json={}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_parse_multiple_logs(self, client):
        """Test parsing multiple log entries"""
        response = client.post(
            '/api/parse-text',
            json={
                'text': 'log1 { id:1 } log2 { id:2 }',
                'decode_base64': False,
                'redact': False
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['results']) == 1  # Returns as single parsed object


class TestDownloadEndpoint:
    """Test download endpoint"""

    def test_download_json(self, client):
        """Test downloading results as JSON"""
        test_data = {"test": "data"}
        response = client.post(
            '/api/download',
            json={
                'data': test_data,
                'filename': 'test.json'
            }
        )
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        assert 'attachment' in response.headers['Content-Disposition']

    def test_download_missing_data(self, client):
        """Test download without data"""
        response = client.post(
            '/api/download',
            json={}
        )
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
