#!/usr/bin/env python3
"""
CLI tool to parse Datadog logs from protobuf text format to JSON

Usage:
    # From string
    python parse_datadog_logs.py "Received event id:..."

    # From file
    python parse_datadog_logs.py -f logfile.txt

    # From stdin
    cat logs.txt | python parse_datadog_logs.py

    # Save to files
    python parse_datadog_logs.py -f logs.txt -o output_dir/

    # Without base64 decoding
    python parse_datadog_logs.py -f logs.txt --no-decode
"""

import sys
import argparse
import json
from pathlib import Path
from datadog_parser_v2 import parse_datadog_logs, format_json_strings


def main():
    parser = argparse.ArgumentParser(
        description='Parse Datadog logs from Protocol Buffer text format to JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse logs from a file
  %(prog)s -f logs.txt

  # Parse logs from stdin
  cat logs.txt | %(prog)s

  # Parse a log string directly
  %(prog)s "Received event id:..."

  # Save parsed logs to separate JSON files
  %(prog)s -f logs.txt -o output_dir/

  # Compact JSON output (no pretty printing)
  %(prog)s -f logs.txt --compact

  # Don't decode base64 fields
  %(prog)s -f logs.txt --no-decode

  # Redact sensitive fields (keeps first/last 4 chars)
  %(prog)s -f logs.txt --redact

  # Redact with custom keep chars (e.g., 6 chars)
  %(prog)s -f logs.txt --redact --keep-chars 6
        """
    )

    parser.add_argument(
        'log_text',
        nargs='?',
        help='Log text to parse (if not using -f or stdin)'
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Input file containing logs'
    )

    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        help='Output directory to save parsed JSON files (saves as log_entry_1.json, etc.)'
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
        help='Redact sensitive fields (keys, tokens, secrets) keeping first/last N chars'
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

    args = parser.parse_args()

    # Get input text
    if args.file:
        log_text = Path(args.file).read_text()
    elif args.log_text:
        log_text = args.log_text
    else:
        # Read from stdin
        if sys.stdin.isatty():
            parser.print_help()
            sys.exit(1)
        log_text = sys.stdin.read()

    # Parse the logs
    try:
        parsed_logs = parse_datadog_logs(
            log_text,
            decode_base64=not args.no_decode,
            redact=args.redact,
            keep_chars=args.keep_chars
        )

        if not parsed_logs:
            print("No log entries found", file=sys.stderr)
            sys.exit(1)

        # Output results
        if args.output_dir:
            # Save to files
            output_path = Path(args.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            json_strings = format_json_strings(parsed_logs, pretty=not args.compact)

            for i, json_str in enumerate(json_strings, 1):
                output_file = output_path / f"log_entry_{i}.json"
                output_file.write_text(json_str)
                print(f"Saved: {output_file}")

            print(f"\nTotal entries parsed: {len(parsed_logs)}")

        elif args.single_json:
            # Output as single JSON array
            if args.compact:
                print(json.dumps(parsed_logs, ensure_ascii=False))
            else:
                print(json.dumps(parsed_logs, indent=2, ensure_ascii=False))

        else:
            # Output to stdout
            json_strings = format_json_strings(parsed_logs, pretty=not args.compact)

            for i, json_str in enumerate(json_strings, 1):
                if len(json_strings) > 1:
                    print(f"=== Log Entry {i} ===")
                print(json_str)
                if i < len(json_strings):
                    print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()