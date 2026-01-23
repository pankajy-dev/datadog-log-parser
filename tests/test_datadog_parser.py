"""
Unit tests for Datadog Log Parser
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datadog_parser_v2 import DatadogLogParser, redact_sensitive_value


class TestDatadogLogParser:
    """Test cases for DatadogLogParser"""

    def test_parse_simple_string(self):
        """Test parsing a simple string value"""
        parser = DatadogLogParser('message:"hello world"')
        result = parser.parse()
        assert result == {"message": "hello world"}

    def test_parse_number(self):
        """Test parsing numeric values"""
        parser = DatadogLogParser("count:42")
        result = parser.parse()
        assert result == {"count": 42}

    def test_parse_boolean_true(self):
        """Test parsing boolean true"""
        parser = DatadogLogParser("opt_out:true")
        result = parser.parse()
        assert result == {"opt_out": True}

    def test_parse_boolean_false(self):
        """Test parsing boolean false"""
        parser = DatadogLogParser("enabled:false")
        result = parser.parse()
        assert result == {"enabled": False}

    def test_parse_nested_structure(self):
        """Test parsing nested structures"""
        text = 'user { name:"John" age:30 }'
        parser = DatadogLogParser(text)
        result = parser.parse()
        assert result == {"user": {"name": "John", "age": 30}}

    def test_parse_array(self):
        """Test parsing arrays"""
        text = 'tags:"python" tags:"flask" tags:"logs"'
        parser = DatadogLogParser(text)
        result = parser.parse()
        assert result == {"tags": ["python", "flask", "logs"]}

    def test_parse_multiple_entries(self):
        """Test parsing multiple log entries"""
        text = 'log1 { id:1 } log2 { id:2 }'
        parser = DatadogLogParser(text)
        result = parser.parse()
        assert "log1" in result and "log2" in result

    def test_base64_decoding(self):
        """Test base64 decoding of values"""
        # "Hello" in base64 is "SGVsbG8="
        parser = DatadogLogParser('data:"SGVsbG8="', decode_base64=True)
        result = parser.parse()
        assert result["data"] == "Hello"

    def test_redaction(self):
        """Test sensitive data redaction"""
        parser = DatadogLogParser('api_key:"secret123456789"', redact=True)
        result = parser.parse()
        assert result["api_key"]["value"].startswith("secr")
        assert result["api_key"]["value"].endswith("6789")
        assert result["api_key"]["_redacted"] is True


class TestRedactionFunction:
    """Test cases for redaction helper function"""

    def test_redact_long_value(self):
        """Test redaction of long values"""
        result = redact_sensitive_value("secretkey123456789", keep_chars=4)
        assert result == "secr...6789"

    def test_redact_short_value(self):
        """Test that short values are not redacted"""
        result = redact_sensitive_value("short", keep_chars=4)
        assert result == "short"

    def test_redact_empty_value(self):
        """Test redaction of empty string"""
        result = redact_sensitive_value("", keep_chars=4)
        assert result == ""

    def test_redact_custom_keep_chars(self):
        """Test redaction with custom keep_chars"""
        result = redact_sensitive_value("verylongsecretkey", keep_chars=2)
        assert result == "ve...ey"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
