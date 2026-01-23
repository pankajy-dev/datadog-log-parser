#!/usr/bin/env python3
"""
CSV Log Extractor - Extract and parse logs from CSV files

Extracts logs from a CSV file's content column and formats them as JSON.
Works with Datadog exports and any CSV format containing structured logs.
"""

import csv
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datadog_parser_v2 import parse_datadog_logs, format_json_strings


def extract_logs_from_csv(
    csv_file: str,
    content_column: str = 'Content',
    include_metadata: bool = True,
    decode_base64: bool = True,
    redact: bool = False,
    keep_chars: int = 4,
    auto_detect: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract and parse logs from CSV file

    Args:
        csv_file: Path to CSV file
        content_column: Name of column containing log content
        include_metadata: Include CSV metadata (Date, Host, Service, etc.) in output
        decode_base64: Decode base64 fields
        redact: Redact sensitive fields
        keep_chars: Characters to keep when redacting
        auto_detect: Auto-detect log format (Datadog protobuf, JSON, etc.)

    Returns:
        List of parsed log entries with optional metadata
    """
    results = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Validate content column exists
        if reader.fieldnames and content_column not in reader.fieldnames:
            available = ', '.join(reader.fieldnames)
            raise ValueError(
                f"Column '{content_column}' not found. Available columns: {available}"
            )

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            content = row.get(content_column, '').strip()

            if not content:
                continue

            # Try to parse the log content
            parsed_content = parse_log_content(
                content,
                decode_base64=decode_base64,
                redact=redact,
                keep_chars=keep_chars,
                auto_detect=auto_detect
            )

            # Build result entry
            if include_metadata:
                # Include all CSV columns as metadata
                entry = {
                    'metadata': {k: v for k, v in row.items() if k != content_column},
                    'log': parsed_content
                }
            else:
                entry = parsed_content

            results.append(entry)

    return results


def parse_log_content(
    content: str,
    decode_base64: bool = True,
    redact: bool = False,
    keep_chars: int = 4,
    auto_detect: bool = True
) -> Any:
    """
    Parse log content based on detected format

    Args:
        content: Raw log content string
        decode_base64: Decode base64 fields
        redact: Redact sensitive fields
        keep_chars: Characters to keep when redacting
        auto_detect: Auto-detect format

    Returns:
        Parsed log data (dict or string)
    """
    if not content:
        return content

    # Try to detect format
    if auto_detect:
        # Check for Datadog protobuf format
        if 'Received' in content and 'event' in content and ':' in content:
            try:
                parsed_logs = parse_datadog_logs(
                    content,
                    decode_base64=decode_base64,
                    redact=redact,
                    keep_chars=keep_chars
                )
                # Return first parsed log if only one, otherwise return list
                return parsed_logs[0] if len(parsed_logs) == 1 else parsed_logs
            except Exception:
                pass

        # Check for JSON format
        if content.startswith('{') or content.startswith('['):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

    # Return as-is if no parser worked
    return content


def count_logs_in_csv(csv_file: str, content_column: str = 'Content') -> Dict[str, int]:
    """
    Count log entries in CSV file

    Args:
        csv_file: Path to CSV file
        content_column: Name of column containing logs

    Returns:
        Statistics about the CSV file
    """
    total_rows = 0
    non_empty_rows = 0
    empty_rows = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_rows += 1
            content = row.get(content_column, '').strip()
            if content:
                non_empty_rows += 1
            else:
                empty_rows += 1

    return {
        'total_rows': total_rows,
        'non_empty_logs': non_empty_rows,
        'empty_logs': empty_rows
    }


def main():
    parser = argparse.ArgumentParser(
        description='Extract and parse logs from CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract logs from CSV
  %(prog)s -f logs.csv

  # Specify custom content column
  %(prog)s -f logs.csv -c Message

  # Without metadata (just the parsed logs)
  %(prog)s -f logs.csv --no-metadata

  # With redaction
  %(prog)s -f logs.csv --redact

  # Save to separate JSON files
  %(prog)s -f logs.csv -o output_dir/

  # Compact JSON output
  %(prog)s -f logs.csv --compact

  # Count logs without extracting
  %(prog)s -f logs.csv --count
        """
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help='Input CSV file'
    )

    parser.add_argument(
        '-c', '--content-column',
        type=str,
        default='Content',
        help='Name of column containing log content (default: Content)'
    )

    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        help='Output directory to save parsed JSON files'
    )

    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Do not include CSV metadata in output (Date, Host, etc.)'
    )

    parser.add_argument(
        '--compact',
        action='store_true',
        help='Output compact JSON (no pretty printing)'
    )

    parser.add_argument(
        '--no-decode',
        action='store_true',
        help='Do not decode base64 encoded fields'
    )

    parser.add_argument(
        '--redact',
        action='store_true',
        help='Redact sensitive fields (keys, tokens, secrets)'
    )

    parser.add_argument(
        '--keep-chars',
        type=int,
        default=4,
        help='Number of characters to keep at start/end when redacting (default: 4)'
    )

    parser.add_argument(
        '--single-json',
        action='store_true',
        help='Output all entries as a single JSON array'
    )

    parser.add_argument(
        '--count',
        action='store_true',
        help='Just count logs without extracting them'
    )

    parser.add_argument(
        '--no-auto-detect',
        action='store_true',
        help='Do not auto-detect log format, keep as raw text'
    )

    args = parser.parse_args()

    # Validate file exists
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        # Count mode
        if args.count:
            stats = count_logs_in_csv(args.file, args.content_column)
            print(json.dumps(stats, indent=2))
            return

        # Extract logs
        logs = extract_logs_from_csv(
            args.file,
            content_column=args.content_column,
            include_metadata=not args.no_metadata,
            decode_base64=not args.no_decode,
            redact=args.redact,
            keep_chars=args.keep_chars,
            auto_detect=not args.no_auto_detect
        )

        if not logs:
            print("No logs found in CSV", file=sys.stderr)
            sys.exit(1)

        # Output results
        if args.output_dir:
            # Save to files
            output_path = Path(args.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            for i, log_entry in enumerate(logs, 1):
                output_file = output_path / f"log_entry_{i}.json"
                json_str = json.dumps(log_entry, indent=2 if not args.compact else None, ensure_ascii=False)
                output_file.write_text(json_str)
                print(f"Saved: {output_file}")

            print(f"\nTotal entries extracted: {len(logs)}")

        elif args.single_json:
            # Output as single JSON array
            if args.compact:
                print(json.dumps(logs, ensure_ascii=False))
            else:
                print(json.dumps(logs, indent=2, ensure_ascii=False))

        else:
            # Output to stdout
            for i, log_entry in enumerate(logs, 1):
                if len(logs) > 1:
                    print(f"=== Log Entry {i} ===")

                if args.compact:
                    print(json.dumps(log_entry, ensure_ascii=False))
                else:
                    print(json.dumps(log_entry, indent=2, ensure_ascii=False))

                if i < len(logs):
                    print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
