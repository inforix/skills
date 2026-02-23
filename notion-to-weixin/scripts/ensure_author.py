#!/usr/bin/env python3
import argparse
import io
import re
from pathlib import Path

FRONT_MATTER_DELIM = "---\n"
AUTHOR_RE = re.compile(r"^author\s*:\s*.*$")
BYLINE_RE = re.compile(r"^\*作者：.*\*\s*$")


def split_front_matter(text: str):
    if not text.startswith(FRONT_MATTER_DELIM):
        return None, text
    end = text.find("\n---\n", len(FRONT_MATTER_DELIM) - 1)
    if end == -1:
        return None, text
    fm = text[len(FRONT_MATTER_DELIM): end]
    rest = text[end + len("\n---\n"):]
    return fm, rest


def build_front_matter(fm: str | None, author: str):
    if fm is None:
        return f"author: {author}\n"
    lines = fm.splitlines()
    updated = False
    new_lines = []
    for line in lines:
        if AUTHOR_RE.match(line):
            new_lines.append(f"author: {author}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"author: {author}")
    return "\n".join(new_lines) + "\n"


def ensure_byline(rest: str, author: str):
    head = rest.lstrip("\n")
    head_lines = head.splitlines()
    for line in head_lines[:20]:
        if BYLINE_RE.match(line.strip()):
            return rest
    byline = f"*作者：{author}*\n\n"
    return byline + rest.lstrip("\n")


def main():
    parser = argparse.ArgumentParser(description="Ensure markdown front matter has author and optional byline.")
    parser.add_argument("--input", required=True, help="Path to markdown file to update")
    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--byline", action="store_true", help="Insert a byline after front matter if missing")
    args = parser.parse_args()

    path = Path(args.input)
    text = path.read_text(encoding="utf-8")

    fm, rest = split_front_matter(text)
    new_fm = build_front_matter(fm, args.author)

    out = io.StringIO()
    out.write(FRONT_MATTER_DELIM)
    out.write(new_fm)
    out.write(FRONT_MATTER_DELIM)
    out.write("\n")
    out.write(rest.lstrip("\n"))

    updated = out.getvalue()
    if args.byline:
        _, body = split_front_matter(updated)
        updated = FRONT_MATTER_DELIM + new_fm + FRONT_MATTER_DELIM + "\n" + ensure_byline(body or "", args.author)

    path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
