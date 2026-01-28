#!/usr/bin/env python3
"""Test the parser with the problematic log"""

import sys
sys.path.insert(0, 'src')

from datadog_parser_v2 import parse_datadog_logs
import json

# The problematic log from the user
test_log = '''Processing bulk external event request with metadata: specversion:"1.0" id:"094f20a6-d622-4da0-80cc-8c24c6716510" source:"https://gauntlet-3.cloudbees.com/cbci/" type:"cloudbees.platform.jenkins.post-build.metadata" subject:"https://gauntlet-3.cloudbees.com/cbci/job/builders/job/URR-pr-builder/job/PR-21670/4" datacontenttype:"application/json" time:{seconds:1768812969 nanos:654137413} data:{provider_info:{provider:"CBCI" run_number:"4" job_name:"builders/URR-pr-builder" build_url:"https://gauntlet-3.cloudbees.com/cbci/job/builders/job/URR-pr-builder/job/PR-21670/4" repositories:{url:"https://github.com/cloudbees/unified-release.git"}}}'''

print("Testing parser with the problematic log...")
print("=" * 80)

try:
    parsed_logs = parse_datadog_logs(test_log, decode_base64=True, redact=False)

    print(f"\n✅ Successfully parsed {len(parsed_logs)} log entry/entries\n")

    for i, log in enumerate(parsed_logs, 1):
        print(f"Log Entry {i}:")
        print("-" * 80)
        print(json.dumps(log, indent=2, ensure_ascii=False))
        print()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()