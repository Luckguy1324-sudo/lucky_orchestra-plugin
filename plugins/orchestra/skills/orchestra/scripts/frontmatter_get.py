#!/usr/bin/env python3
"""
frontmatter_get.py — read a single value from a Markdown YAML frontmatter block

Usage:
  frontmatter_get.py <file.md> <key>

Behavior:
  - Reads the first '---' delimited YAML frontmatter block at the top of <file.md>
  - Prints the value of <key> to stdout
  - Exits 0 on success, 1 if frontmatter missing, 2 if key missing

Replaces `yq` dependency. Works with Python 3.8+ stdlib alone if PyYAML is
absent (uses a minimal parser sufficient for the keys this plugin uses).
"""
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> dict | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    body = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line)

    raw = "\n".join(body)
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(raw)
        return data if isinstance(data, dict) else None
    except ImportError:
        return parse_minimal_yaml(raw)


def parse_minimal_yaml(text: str) -> dict:
    """Best-effort YAML parser for simple key: value lines and key: [list]."""
    out: dict = {}
    current_list_key = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if current_list_key and (line.startswith("  - ") or line.startswith("- ")):
            item = line.strip()[2:].strip()
            item = item.strip("'\"")
            out.setdefault(current_list_key, []).append(item)
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            current_list_key = key
            out[key] = []
        else:
            current_list_key = None
            value = value.strip("'\"")
            out[key] = value
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: frontmatter_get.py <file.md> <key>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    key = sys.argv[2]

    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 1

    fm = parse_frontmatter(path.read_text(encoding="utf-8"))
    if fm is None:
        print("frontmatter not found", file=sys.stderr)
        return 1

    if key not in fm:
        print(f"key not in frontmatter: {key}", file=sys.stderr)
        return 2

    value = fm[key]
    if isinstance(value, list):
        for v in value:
            print(v)
    else:
        print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
