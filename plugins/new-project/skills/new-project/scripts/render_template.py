#!/usr/bin/env python3
"""Render a template file by replacing {{KEY}} placeholders with literal values.

Usage: render_template.py <src> <dest> KEY=VALUE [KEY=VALUE ...]

Uses plain string replacement (not a template engine) so values may contain
any character - slashes, ampersands, newlines - without escaping.
"""
import sys


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: render_template.py <src> <dest> KEY=VALUE [...]", file=sys.stderr)
        sys.exit(1)

    src, dest = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    for pair in sys.argv[3:]:
        key, sep, value = pair.partition("=")
        if not sep:
            print(f"Malformed KEY=VALUE argument: {pair!r}", file=sys.stderr)
            sys.exit(1)
        text = text.replace("{{" + key + "}}", value)

    open(dest, "w", encoding="utf-8").write(text)


if __name__ == "__main__":
    main()
