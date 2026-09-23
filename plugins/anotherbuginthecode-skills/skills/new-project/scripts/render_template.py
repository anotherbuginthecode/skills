#!/usr/bin/env python3
"""Render a template file: strip/keep {{#FLAG}}...{{/FLAG}} conditional
blocks, then replace {{KEY}} placeholders with literal values.

Usage: render_template.py <src> <dest> KEY=VALUE [KEY=VALUE ...]

A block wrapped in {{#FLAG}}...{{/FLAG}} is kept (markers removed, content
kept) when FLAG=true is passed, and dropped entirely otherwise - including
when FLAG is not passed at all. Plain {{KEY}} substitution then runs on
whatever text remains, via literal string replacement (not a template
engine), so values may contain any character - slashes, ampersands,
newlines - without escaping.
"""
import re
import sys


def apply_conditionals(text: str, values: dict[str, str]) -> str:
    pattern = re.compile(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL)

    def replace(match: re.Match) -> str:
        flag, body = match.group(1), match.group(2)
        return body if values.get(flag) == "true" else ""

    return pattern.sub(replace, text)


def apply_substitutions(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def collapse_blank_lines(text: str) -> str:
    """A dropped conditional block leaves its surrounding blank lines behind
    - collapse three or more consecutive newlines down to one blank line."""
    return re.sub(r"\n{3,}", "\n\n", text)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: render_template.py <src> <dest> KEY=VALUE [...]", file=sys.stderr)
        sys.exit(1)

    src, dest = sys.argv[1], sys.argv[2]
    values: dict[str, str] = {}
    for pair in sys.argv[3:]:
        key, sep, value = pair.partition("=")
        if not sep:
            print(f"Malformed KEY=VALUE argument: {pair!r}", file=sys.stderr)
            sys.exit(1)
        values[key] = value

    text = open(src, encoding="utf-8").read()
    text = apply_conditionals(text, values)
    text = apply_substitutions(text, values)
    text = collapse_blank_lines(text)
    open(dest, "w", encoding="utf-8").write(text)


if __name__ == "__main__":
    main()
