"""
Unit tests for CSV Log Extractor
"""

import pytest
import sys
import tempfile
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csv_log_extractor import extract_logs_from_csv


class TestCSVLogExtractor:
    """Test cases for CSV log extraction"""

    def create_test_csv(self, rows):
        """Helper to create a temporary CSV file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        writer = csv.DictWriter(temp_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        temp_file.close()
        return temp_file.name

    def test_basic_csv_extraction(self):
        """Test basic CSV log extraction"""
        rows = [
            {
                'Date': '2024-01-23',
                'Host': 'server1',
                'Service': 'api',
                'Content': 'message:"test log"'
            }
        ]
        csv_file = self.create_test_csv(rows)

        results = extract_logs_from_csv(csv_file, include_metadata=False)

        assert len(results) == 1
        assert results[0]["message"] == "test log"

        # Cleanup
        Path(csv_file).unlink()

    def test_csv_with_metadata(self):
        """Test CSV extraction with metadata preservation"""
        rows = [
            {
                'Date': '2024-01-23',
                'Host': 'server1',
                'Service': 'api',
                'Content': 'id:123'
            }
        ]
        csv_file = self.create_test_csv(rows)

        results = extract_logs_from_csv(csv_file, include_metadata=True)

        assert len(results) == 1
        assert results[0]["_metadata"]["Date"] == "2024-01-23"
        assert results[0]["_metadata"]["Host"] == "server1"
        assert results[0]["_metadata"]["Service"] == "api"
        assert results[0]["id"] == 123

        # Cleanup
        Path(csv_file).unlink()

    def test_multiple_rows(self):
        """Test extraction of multiple log entries"""
        rows = [
            {
                'Date': '2024-01-23',
                'Host': 'server1',
                'Service': 'api',
                'Content': 'log_id:1'
            },
            {
                'Date': '2024-01-23',
                'Host': 'server2',
                'Service': 'web',
                'Content': 'log_id:2'
            }
        ]
        csv_file = self.create_test_csv(rows)

        results = extract_logs_from_csv(csv_file, include_metadata=False)

        assert len(results) == 2
        assert results[0]["log_id"] == 1
        assert results[1]["log_id"] == 2

        # Cleanup
        Path(csv_file).unlink()

    def test_csv_with_boolean(self):
        """Test CSV extraction with boolean values"""
        rows = [
            {
                'Date': '2024-01-23',
                'Host': 'server1',
                'Service': 'api',
                'Content': 'enabled:true disabled:false'
            }
        ]
        csv_file = self.create_test_csv(rows)

        results = extract_logs_from_csv(csv_file, include_metadata=False)

        assert len(results) == 1
        assert results[0]["enabled"] is True
        assert results[0]["disabled"] is False

        # Cleanup
        Path(csv_file).unlink()

    def test_csv_with_redaction(self):
        """Test CSV extraction with redaction enabled"""
        rows = [
            {
                'Date': '2024-01-23',
                'Host': 'server1',
                'Service': 'api',
                'Content': 'api_key:"secretkey123456789"'
            }
        ]
        csv_file = self.create_test_csv(rows)

        results = extract_logs_from_csv(csv_file, redact=True, keep_chars=4)

        assert len(results) == 1
        assert results[0]["api_key"]["_redacted"] is True
        assert "secr" in results[0]["api_key"]["value"]
        assert "6789" in results[0]["api_key"]["value"]

        # Cleanup
        Path(csv_file).unlink()

    def test_empty_csv(self):
        """Test handling of empty CSV"""
        rows = []
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        temp_file.write("Date,Host,Service,Content\n")
        temp_file.close()

        results = extract_logs_from_csv(temp_file.name)

        assert len(results) == 0

        # Cleanup
        Path(temp_file.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
