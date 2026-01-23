#!/usr/bin/env python3
"""
Datadog Log Parser - Converts Protocol Buffer text format to JSON
"""

import re
import json
import base64
from typing import List, Dict, Any


def parse_protobuf_text(text: str) -> Dict[str, Any]:
    """
    Parse protobuf text format to Python dict
    """
    result = {}

    # Remove "Received OcPreRegisterControllerMetadataType event " prefix if present
    text = re.sub(r'^Received\s+\w+\s+event\s+', '', text.strip())

    # Stack to handle nested structures
    stack = [result]
    current_key = None

    # Tokenize the input
    tokens = re.findall(r'(\w+):|{|}|"([^"]*)"|(\d+)', text)

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token[0]:  # Key
            current_key = token[0]
            # Look ahead to see if next is '{'
            if i + 1 < len(tokens) and tokens[i + 1] == ('{', '', ''):
                stack[-1][current_key] = {}
                stack.append(stack[-1][current_key])
                i += 2  # Skip the '{'
                continue
        elif token == ('{', '', ''):  # Opening brace for repeated fields
            if current_key:
                if current_key not in stack[-1]:
                    stack[-1][current_key] = []
                new_dict = {}
                stack[-1][current_key].append(new_dict)
                stack.append(new_dict)
            i += 1
            continue
        elif token == ('}', '', ''):  # Closing brace
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue
        elif token[1]:  # String value
            if current_key:
                value = token[1]
                stack[-1][current_key] = value
                current_key = None
        elif token[2]:  # Number value
            if current_key:
                stack[-1][current_key] = int(token[2])
                current_key = None

        i += 1

    return result


def parse_protobuf_text_advanced(text: str) -> Dict[str, Any]:
    """
    More robust parser for protobuf text format
    """
    result = {}

    # Remove prefix
    text = re.sub(r'^Received\s+\w+\s+event\s+', '', text.strip())

    def parse_value(s: str, pos: int) -> tuple[Any, int]:
        """Parse a value starting at position pos, return (value, new_position)"""
        s = s[pos:].lstrip()
        pos = 0

        # Check for opening brace (nested message)
        if s.startswith('{'):
            obj = {}
            pos = 1
            while pos < len(s):
                s_remaining = s[pos:].lstrip()
                pos = len(s) - len(s_remaining)

                if s[pos] == '}':
                    return obj, pos + 1

                # Parse key
                match = re.match(r'(\w+):', s[pos:])
                if match:
                    key = match.group(1)
                    pos += match.end()
                    value, new_pos = parse_value(s, pos)
                    pos = new_pos

                    # Handle repeated fields
                    if key in obj:
                        if not isinstance(obj[key], list):
                            obj[key] = [obj[key]]
                        obj[key].append(value)
                    else:
                        obj[key] = value
                else:
                    break

            return obj, pos + 1

        # Check for string value
        elif s.startswith('"'):
            match = re.match(r'"([^"]*)"', s)
            if match:
                return match.group(1), match.end()

        # Check for number
        else:
            match = re.match(r'(\d+)', s)
            if match:
                return int(match.group(1)), match.end()

        return None, pos

    pos = 0
    while pos < len(text):
        text_remaining = text[pos:].lstrip()
        pos = len(text) - len(text_remaining)

        if pos >= len(text):
            break

        # Parse key
        match = re.match(r'(\w+):', text[pos:])
        if match:
            key = match.group(1)
            pos += match.end()
            value, new_pos = parse_value(text, pos)
            pos = new_pos
            result[key] = value
        else:
            break

    return result


def decode_base64_keys(data: Dict[str, Any], keys_to_decode: List[str] = ['public_key']) -> Dict[str, Any]:
    """
    Decode base64 encoded values in the dictionary
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in keys_to_decode and isinstance(value, str):
                try:
                    decoded = base64.b64decode(value).decode('utf-8')
                    result[key] = decoded
                    result[f"{key}_base64"] = value  # Keep original
                except:
                    result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = decode_base64_keys(value, keys_to_decode)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [decode_base64_keys(item, keys_to_decode) for item in data]
    return data


def split_log_entries(log_text: str) -> List[str]:
    """
    Split multiple log entries from a single text
    """
    # Split on the pattern "Received ... event"
    pattern = r'(?=Received\s+\w+\s+event\s+)'
    entries = re.split(pattern, log_text)
    return [entry.strip() for entry in entries if entry.strip()]


def parse_datadog_logs(log_text: str, decode_base64: bool = True) -> List[Dict[str, Any]]:
    """
    Parse Datadog logs and return list of JSON objects

    Args:
        log_text: Raw log text from Datadog (can contain multiple entries)
        decode_base64: Whether to decode base64 encoded fields

    Returns:
        List of parsed JSON objects
    """
    entries = split_log_entries(log_text)
    results = []

    for entry in entries:
        try:
            parsed = parse_protobuf_text_advanced(entry)
            if decode_base64:
                parsed = decode_base64_keys(parsed)
            results.append(parsed)
        except Exception as e:
            print(f"Error parsing entry: {e}")
            print(f"Entry: {entry[:100]}...")

    return results


def main():
    """
    Example usage
    """
    # Example log from Datadog
    sample_log = '''Received OcPreRegisterControllerMetadataType event id:"3a92e52d-4caa-4e08-8cf4-1afd93b8c001" subject:"http://34.23.204.255.nip.io/cjoc/" type:"cloudbees.platform.jenkins.oc.pre-register-controller" source:"http://34.23.204.255.nip.io/cjoc/" specversion:"1.0" time:{seconds:1768568725 nanos:86833482} datacontenttype:"application/json" data:{provider_info:{provider:"OC"} metadata:{reconcile_type:"controller" controllers:{name:"kmcontroller" url:"http://34.23.204.255.nip.io/kmcontroller/" public_key:"LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF0a0thUWEzSGliWUQ1Z0V5UThONgoyVTliTG10eTdsU1ZuSnlyVFRaaUR1OGNOcjA4SVBWdGRkdit2TEtDV2xUOWx5blh2TERIcnRhekVjWDRwSW9lCkJXck9QOVNhVVcvNCs0S3pzdEppWTJLam9mOFFXdnEwWjhPNndvSkJ1NEw3cUhUMDlXQjFOdU1oNFloblFURUMKajNOMDhRNnZqdHBmNUQwS1dtclFzL0dXdXAvUlJIUklvQTJsRWpyM2IyVHFoaDdiTFRhRHpSVXdlZm8vYVdyWQpuUzI4RGNMUEJSeEZMejZUcFhUZncvZTQwQmtMMzhDaHhiMWl2UzkvTk9NUDcvc2h6VnQxdW91eEFaUXBlN3Y0ClBkRFB3ZmsvM296a3VBSEsrYVhScTI0bkd1a3VqZUZmbURjdThyRU9iNG5ZT0tUZWw0SDNKd1htZUVmS3RIZmUKUHdJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==" operation:"create"}}}

Received OcPreRegisterControllerMetadataType event id:"717aaf67-b18b-40d2-8c22-644fcab107aa" subject:"http://34.23.204.255.nip.io/cjoc/" type:"cloudbees.platform.jenkins.oc.pre-register-controller" source:"http://34.23.204.255.nip.io/cjoc/" specversion:"1.0" time:{seconds:1768615571 nanos:40462313} datacontenttype:"application/json" data:{provider_info:{provider:"OC"} metadata:{reconcile_type:"controller" controllers:{name:"kmcontroller" url:"http://34.23.204.255.nip.io/kmcontroller/" public_key:"LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF0a0thUWEzSGliWUQ1Z0V5UThONgoyVTliTG10eTdsU1ZuSnlyVFRaaUR1OGNOcjA4SVBWdGRkdit2TEtDV2xUOWx5blh2TERIcnRhekVjWDRwSW9lCkJXck9QOVNhVVcvNCs0S3pzdEppWTJLam9mOFFXdnEwWjhPNndvSkJ1NEw3cUhUMDlXQjFOdU1oNFloblFURUMKajNOMDhRNnZqdHBmNUQwS1dtclFzL0dXdXAvUlJIUklvQTJsRWpyM2IyVHFoaDdiTFRhRHpSVXdlZm8vYVdyWQpuUzI4RGNMUEJSeEZMejZUcFhUZncvZTQwQmtMMzhDaHhiMWl2UzkvTk9NUDcvc2h6VnQxdW91eEFaUXBlN3Y0ClBkRFB3ZmsvM296a3VBSEsrYVhScTI0bkd1a3VqZUZmbURjdThyRU9iNG5ZT0tUZWw0SDNKd1htZUVmS3RIZmUKUHdJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==" operation:"create"}}}'''

    # Parse the logs
    parsed_logs = parse_datadog_logs(sample_log, decode_base64=True)

    # Print each log entry as formatted JSON
    for i, log in enumerate(parsed_logs, 1):
        print(f"=== Log Entry {i} ===")
        print(json.dumps(log, indent=2))
        print()


if __name__ == "__main__":
    main()