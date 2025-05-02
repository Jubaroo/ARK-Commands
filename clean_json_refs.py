#!/usr/bin/env python3
import re
import json
import sys
from pathlib import Path
from typing import Any

# regex matching exactly :contentReference[oaicite:<digits>]{index=<digits>}
_pattern = re.compile(r':contentReference\[oaicite:\d+\]\{index=\d+\}')

def clean_value(value: Any) -> Any:
    """
    Recursively walk through the JSON structure and remove all matches
    of our pattern from any string.
    """
    if isinstance(value, str):
        # strip out all occurrences in this string
        return _pattern.sub('', value)
    elif isinstance(value, list):
        return [clean_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: clean_value(v) for k, v in value.items()}
    else:
        return value

def clean_json_file(src_path: Path, dst_path: Path) -> None:
    data = json.loads(src_path.read_text(encoding='utf-8'))
    cleaned = clean_value(data)
    dst_path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Cleaned JSON written to {dst_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clean_json_refs.py <input.json> <output.json>")
        sys.exit(1)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    if not src.is_file():
        print(f"Error: {src} does not exist or is not a file.")
        sys.exit(1)

    clean_json_file(src, dst)
