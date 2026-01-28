#!/usr/bin/env python3
"""
Improved Datadog Log Parser - Converts Protocol Buffer text format to JSON
Handles nested structures and repeated fields properly
"""

import re
import json
import base64
from typing import List, Dict, Any, Tuple


class ProtobufTextParser:
    """Parser for Protocol Buffer text format"""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def skip_whitespace(self):
        """Skip whitespace characters"""
        while self.pos < self.length and self.text[self.pos] in ' \t\n\r':
            self.pos += 1

    def peek(self) -> str:
        """Peek at current character without consuming"""
        self.skip_whitespace()
        if self.pos < self.length:
            return self.text[self.pos]
        return ''

    def consume(self, expected: str = None) -> str:
        """Consume and return current character"""
        self.skip_whitespace()
        if self.pos >= self.length:
            return ''
        char = self.text[self.pos]
        if expected and char != expected:
            raise ValueError(f"Expected '{expected}' but got '{char}' at position {self.pos}")
        self.pos += 1
        return char

    def parse_string(self) -> str:
        """Parse a quoted string"""
        self.consume('"')
        start = self.pos
        while self.pos < self.length and self.text[self.pos] != '"':
            if self.text[self.pos] == '\\':
                self.pos += 2  # Skip escaped character
            else:
                self.pos += 1
        result = self.text[start:self.pos]
        self.consume('"')
        return result

    def parse_number(self) -> int:
        """Parse a number"""
        start = self.pos
        while self.pos < self.length and self.text[self.pos].isdigit():
            self.pos += 1
        return int(self.text[start:self.pos])

    def parse_boolean(self) -> bool:
        """Parse a boolean value (true/false)"""
        if self.text[self.pos:self.pos+4] == 'true':
            self.pos += 4
            return True
        elif self.text[self.pos:self.pos+5] == 'false':
            self.pos += 5
            return False
        else:
            raise ValueError(f"Expected boolean at position {self.pos}")

    def parse_identifier(self) -> str:
        """Parse an identifier (field name)"""
        start = self.pos
        while self.pos < self.length and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return self.text[start:self.pos]

    def parse_value(self) -> Any:
        """Parse a value (string, number, boolean, or nested message)"""
        char = self.peek()

        if char == '"':
            return self.parse_string()
        elif char == '{':
            return self.parse_message()
        elif char.isdigit() or char == '-':
            return self.parse_number()
        elif char == 't' or char == 'f':
            # Check for boolean (true/false)
            return self.parse_boolean()
        else:
            raise ValueError(f"Unexpected character '{char}' at position {self.pos}")

    def parse_message(self) -> Dict[str, Any]:
        """Parse a nested message (between braces)"""
        result = {}
        self.consume('{')

        while self.peek() != '}':
            # Parse field name
            field_name = self.parse_identifier()
            self.consume(':')

            # Parse field value
            value = self.parse_value()

            # Handle repeated fields (convert to list)
            if field_name in result:
                if not isinstance(result[field_name], list):
                    result[field_name] = [result[field_name]]
                result[field_name].append(value)
            else:
                result[field_name] = value

        self.consume('}')
        return result

    def parse(self) -> Dict[str, Any]:
        """Parse the entire protobuf text format"""
        # Try to find where the actual protobuf data starts
        # Look for a field followed by a value (field:"value" or field:{...} or field:number)
        # This distinguishes actual protobuf fields from prefix text like "metadata:"
        match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*):\s*["{0-9]', self.text)
        if match:
            # Start parsing from the field name (not the value)
            self.pos = match.start()
        else:
            # Fallback: look for any field:value pattern
            match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*):', self.text)
            if match:
                self.pos = match.start()

        result = {}

        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length:
                break

            # Parse field name
            field_name = self.parse_identifier()
            if not field_name:
                break

            self.consume(':')

            # Parse field value
            value = self.parse_value()

            # Handle repeated fields
            if field_name in result:
                if not isinstance(result[field_name], list):
                    result[field_name] = [result[field_name]]
                result[field_name].append(value)
            else:
                result[field_name] = value

        return result


def redact_sensitive_value(value: str, keep_chars: int = 4) -> str:
    """
    Redact sensitive value keeping first and last N characters

    Args:
        value: String to redact
        keep_chars: Number of characters to keep at start and end (default: 4)

    Returns:
        Redacted string like "ABCD...WXYZ"
    """
    if not isinstance(value, str):
        return value

    if len(value) <= keep_chars * 2:
        return value  # Too short to redact meaningfully

    return f"{value[:keep_chars]}...{value[-keep_chars:]}"


def redact_sensitive_fields(data: Any, keys_to_redact: List[str] = None, keep_chars: int = 4) -> Any:
    """
    Recursively redact sensitive fields in the dictionary

    Args:
        data: Data structure to process
        keys_to_redact: List of keys whose values should be redacted
        keep_chars: Number of characters to keep at start and end

    Returns:
        Data with sensitive fields redacted
    """
    if keys_to_redact is None:
        keys_to_redact = ['public_key', 'private_key', 'secret', 'token', 'api_key',
                          'password', 'credential', 'auth', 'authorization']

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Check if key name suggests sensitive data (case-insensitive)
            key_lower = key.lower()
            should_redact = any(sensitive in key_lower for sensitive in keys_to_redact)

            if should_redact and isinstance(value, str):
                result[key] = redact_sensitive_value(value, keep_chars)
                result[f"{key}_redacted"] = True
            elif isinstance(value, (dict, list)):
                result[key] = redact_sensitive_fields(value, keys_to_redact, keep_chars)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [redact_sensitive_fields(item, keys_to_redact, keep_chars) for item in data]
    return data


def decode_base64_fields(data: Any, keys_to_decode: List[str] = None) -> Any:
    """
    Recursively decode base64 encoded values in the dictionary

    Args:
        data: Data structure to process
        keys_to_decode: List of keys whose values should be decoded (default: ['public_key'])

    Returns:
        Data with base64 fields decoded
    """
    if keys_to_decode is None:
        keys_to_decode = ['public_key']

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in keys_to_decode and isinstance(value, str):
                try:
                    decoded = base64.b64decode(value).decode('utf-8')
                    result[key] = decoded
                    result[f"{key}_base64"] = value  # Keep original
                except Exception:
                    result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = decode_base64_fields(value, keys_to_decode)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [decode_base64_fields(item, keys_to_decode) for item in data]
    return data


def split_log_entries(log_text: str) -> List[str]:
    """
    Split multiple log entries from a single text

    Args:
        log_text: Raw log text that may contain multiple entries

    Returns:
        List of individual log entry strings
    """
    # Try multiple splitting patterns for different log formats
    patterns = [
        r'(?=Received\s+\w+\s+event\s+)',           # "Received ... event"
        r'(?=Processing\s+.*?\s+metadata:\s+)',     # "Processing ... metadata:"
        r'(?=\n\s*[a-zA-Z_][a-zA-Z0-9_]*:)',        # New line followed by field:value
    ]

    entries = [log_text]  # Start with the whole text

    # Try each pattern
    for pattern in patterns:
        split_result = re.split(pattern, log_text)
        split_result = [entry.strip() for entry in split_result if entry.strip()]
        # Use this split if it found multiple entries
        if len(split_result) > len(entries):
            entries = split_result

    return entries


def parse_datadog_logs(log_text: str, decode_base64: bool = True, redact: bool = False,
                       keep_chars: int = 4) -> List[Dict[str, Any]]:
    """
    Parse Datadog logs and return list of JSON objects

    Args:
        log_text: Raw log text from Datadog (can contain multiple entries)
        decode_base64: Whether to decode base64 encoded fields (default: True)
        redact: Whether to redact sensitive fields (default: False)
        keep_chars: Number of characters to keep at start/end when redacting (default: 4)

    Returns:
        List of parsed JSON objects
    """
    # First, try to detect if the entire text is JSON
    stripped_text = log_text.strip()
    if stripped_text.startswith('{') or stripped_text.startswith('['):
        try:
            json_data = json.loads(stripped_text)
            if isinstance(json_data, dict):
                json_data = [json_data]

            # Process JSON data with decode_base64 and redact if needed
            for item in json_data:
                if decode_base64:
                    item = decode_base64_fields(item)
                if redact:
                    item = redact_sensitive_fields(item, keep_chars=keep_chars)

            return json_data if isinstance(json_data, list) else [json_data]
        except json.JSONDecodeError:
            # Not valid JSON, continue with protobuf parsing
            pass

    entries = split_log_entries(log_text)
    results = []

    for i, entry in enumerate(entries):
        try:
            # Check if this individual entry is JSON
            entry_stripped = entry.strip()
            if entry_stripped.startswith('{'):
                try:
                    parsed = json.loads(entry_stripped)

                    if decode_base64:
                        parsed = decode_base64_fields(parsed)
                    if redact:
                        parsed = redact_sensitive_fields(parsed, keep_chars=keep_chars)

                    results.append(parsed)
                    continue
                except json.JSONDecodeError:
                    pass

            # Try parsing as protobuf text format
            parser = ProtobufTextParser(entry)
            parsed = parser.parse()

            # If parsing resulted in empty dict, treat as plain text
            if not parsed:
                parsed = {"message": entry, "format": "plain_text"}
            else:
                if decode_base64:
                    parsed = decode_base64_fields(parsed)
                if redact:
                    parsed = redact_sensitive_fields(parsed, keep_chars=keep_chars)

            results.append(parsed)
        except Exception as e:
            # If parsing fails, store the raw entry as plain text
            print(f"Error parsing entry {i + 1}: {e}")
            print(f"Entry snippet: {entry[:200]}...")
            results.append({
                "message": entry,
                "format": "plain_text",
                "parse_error": str(e)
            })

    return results


def format_json_strings(parsed_logs: List[Dict[str, Any]], pretty: bool = True) -> List[str]:
    """
    Convert parsed logs to JSON strings

    Args:
        parsed_logs: List of parsed log dictionaries
        pretty: Whether to pretty-print JSON (default: True)

    Returns:
        List of JSON strings
    """
    if pretty:
        return [json.dumps(log, indent=2, ensure_ascii=False) for log in parsed_logs]
    else:
        return [json.dumps(log, ensure_ascii=False) for log in parsed_logs]


def main():
    """Example usage with the provided sample data"""

    sample_log = '''Received OcPreRegisterControllerMetadataType event id:"3a92e52d-4caa-4e08-8cf4-1afd93b8c001" subject:"http://34.23.204.255.nip.io/cjoc/" type:"cloudbees.platform.jenkins.oc.pre-register-controller" source:"http://34.23.204.255.nip.io/cjoc/" specversion:"1.0" time:{seconds:1768568725 nanos:86833482} datacontenttype:"application/json" data:{provider_info:{provider:"OC"} metadata:{reconcile_type:"controller" controllers:{name:"kmcontroller" url:"http://34.23.204.255.nip.io/kmcontroller/" public_key:"LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF0a0thUWEzSGliWUQ1Z0V5UThONgoyVTliTG10eTdsU1ZuSnlyVFRaaUR1OGNOcjA4SVBWdGRkdit2TEtDV2xUOWx5blh2TERIcnRhekVjWDRwSW9lCkJXck9QOVNhVVcvNCs0S3pzdEppWTJLam9mOFFXdnEwWjhPNndvSkJ1NEw3cUhUMDlXQjFOdU1oNFloblFURUMKajNOMDhRNnZqdHBmNUQwS1dtclFzL0dXdXAvUlJIUklvQTJsRWpyM2IyVHFoaDdiTFRhRHpSVXdlZm8vYVdyWQpuUzI4RGNMUEJSeEZMejZUcFhUZncvZTQwQmtMMzhDaHhiMWl2UzkvTk9NUDcvc2h6VnQxdW91eEFaUXBlN3Y0ClBkRFB3ZmsvM296a3VBSEsrYVhScTI0bkd1a3VqZUZmbURjdThyRU9iNG5ZT0tUZWw0SDNKd1htZUVmS3RIZmUKUHdJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==" operation:"create"}}}

Received OcPreRegisterControllerMetadataType event id:"717aaf67-b18b-40d2-8c22-644fcab107aa" subject:"http://34.23.204.255.nip.io/cjoc/" type:"cloudbees.platform.jenkins.oc.pre-register-controller" source:"http://34.23.204.255.nip.io/cjoc/" specversion:"1.0" time:{seconds:1768615571 nanos:40462313} datacontenttype:"application/json" data:{provider_info:{provider:"OC"} metadata:{reconcile_type:"controller" controllers:{name:"kmcontroller" url:"http://34.23.204.255.nip.io/kmcontroller/" public_key:"LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF0a0thUWEzSGliWUQ5Z0V5UThONgoyVTliTG10eTdsU1ZuSnlyVFRaaUR1OGNOcjA4SVBWdGRkdit2TEtDV2xUOWx5blh2TERIcnRhekVjWDRwSW9lCkJXck9QOVNhVVcvNCs0S3pzdEppWTJLam9mOFFXdnEwWjhPNndvSkJ1NEw3cUhUMDlXQjFOdU1oNFloblFURUMKajNOMDhRNnZqdHBmNUQwS1dtclFzL0dXdXAvUlJIUklvQTJsRWpyM2IyVHFoaDdiTFRhRHpSVXdlZm8vYVdyWQpuUzI4RGNMUEJSeEZMejZUcFhUZncvZTQwQmtMMzhDaHhiMWl2UzkvTk9NUDcvc2h6VnQxdW91eEFaUXBlN3Y0ClBkRFB3ZmsvM296a3VBSEsrYVhScTI0bkd1a3VqZUZmbURjdThyRU9iNG5ZT0tUZWw0SDNKd1htZUVmS3RIZmUKUHdJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==" operation:"create"}}}'''

    print("=" * 80)
    print("Datadog Log Parser - Protobuf Text to JSON Converter")
    print("=" * 80)
    print()

    # Parse the logs without redaction
    parsed_logs = parse_datadog_logs(sample_log, decode_base64=True, redact=False)

    print(f"Found {len(parsed_logs)} log entries\n")

    # Get formatted JSON strings
    json_strings = format_json_strings(parsed_logs, pretty=True)

    # Print each log entry
    for i, json_str in enumerate(json_strings, 1):
        print(f"{'=' * 80}")
        print(f"Log Entry {i} (without redaction)")
        print(f"{'=' * 80}")
        print(json_str)
        print()

    # Also demonstrate with redaction
    print("\n" + "=" * 80)
    print("Example with REDACTION enabled")
    print("=" * 80)
    print()

    parsed_logs_redacted = parse_datadog_logs(sample_log, decode_base64=True, redact=True, keep_chars=4)
    json_strings_redacted = format_json_strings(parsed_logs_redacted, pretty=True)

    # Print first entry with redaction
    print("Log Entry 1 (with redaction - keeps first/last 4 chars)")
    print("=" * 80)
    print(json_strings_redacted[0])
    print()

    # Also save to files
    for i, json_str in enumerate(json_strings, 1):
        filename = f"log_entry_{i}.json"
        with open(filename, 'w') as f:
            f.write(json_str)
        print(f"Saved to: {filename}")


if __name__ == "__main__":
    main()
