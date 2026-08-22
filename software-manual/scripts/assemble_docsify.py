#!/usr/bin/env python3
"""Assemble Markdown sections and screenshots into one offline HTML manual."""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any


SCREENSHOT_RE = re.compile(r'^\s*<!--\s*SCREENSHOT:\s*(.*?)\s*-->\s*$')
ATTR_RE = re.compile(r'([A-Za-z_][\w-]*)="([^"]*)"')
HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$')
LIST_RE = re.compile(r'^\s*([-+*]|\d+\.)\s+(.+)$')
FENCE_RE = re.compile(r'^\s*```\s*([\w+-]*)\s*$')
SAFE_LINK_SCHEMES = ("http://", "https://", "mailto:", "#", "/", "./", "../")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an offline Docsify-style single-file manual")
    parser.add_argument("--work-dir", required=True, type=Path, help="Manual working directory")
    parser.add_argument("--skill-dir", type=Path, help="Skill directory; defaults to script parent")
    parser.add_argument("--config", type=Path, help="manual-config.json path")
    parser.add_argument("--sections-dir", type=Path, help="Markdown section directory")
    parser.add_argument("--screenshots-dir", type=Path, help="Screenshot directory")
    parser.add_argument("--output", type=Path, help="Final HTML path")
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    return parser.parse_args()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def safe_identifier(value: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-")
    return value or fallback


def inline_markdown(text: str) -> str:
    escaped = html.escape(text, quote=False)
    code_tokens: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        code_tokens.append(f"<code>{html.escape(html.unescape(match.group(1)))}</code>")
        return f"\x00CODE{len(code_tokens) - 1}\x00"

    escaped = re.sub(r"`([^`]+)`", save_code, escaped)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        raw_href = html.unescape(match.group(2)).strip()
        if not raw_href.lower().startswith(SAFE_LINK_SCHEMES):
            return label
        href = html.escape(raw_href, quote=True)
        return f'<a href="{href}">{label}</a>'

    escaped = re.sub(r"\[([^]]+)]\(([^)]+)\)", link, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    for index, token in enumerate(code_tokens):
        escaped = escaped.replace(f"\x00CODE{index}\x00", token)
    return escaped


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def load_screenshot_manifest(directory: Path) -> dict[str, dict[str, Any]]:
    manifest_path = directory / "screenshots-manifest.json"
    data = read_json(manifest_path, {"screenshots": []}) or {"screenshots": []}
    items = data.get("screenshots", data if isinstance(data, list) else [])
    result: dict[str, dict[str, Any]] = {}
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("id"):
                result[str(item["id"])] = item
    return result


def screenshot_html(
    attributes: dict[str, str], directory: Path, manifest: dict[str, dict[str, Any]], warnings: list[str]
) -> str:
    screenshot_id = attributes.get("id", "").strip()
    description = attributes.get("description", screenshot_id or "界面截图")
    if not screenshot_id:
        warnings.append("screenshot marker is missing id")
        return '<div class="screenshot-placeholder">待补截图：缺少 ID</div>'
    item = manifest.get(screenshot_id, {})
    filename = str(item.get("file") or f"{screenshot_id}.png")
    candidate = (directory / filename).resolve()
    try:
        candidate.relative_to(directory.resolve())
    except ValueError:
        warnings.append(f"screenshot path escapes directory: {screenshot_id}")
        return f'<div class="screenshot-placeholder">待补截图：{html.escape(description)}</div>'
    if item.get("status") not in (None, "captured") or not candidate.is_file():
        warnings.append(f"unresolved screenshot: {screenshot_id}")
        return f'<div class="screenshot-placeholder" data-screenshot-id="{html.escape(screenshot_id, quote=True)}">待补截图：{html.escape(description)}</div>'
    mime = mimetypes.guess_type(candidate.name)[0] or "image/png"
    if not mime.startswith("image/"):
        warnings.append(f"unsupported screenshot MIME type: {candidate.name}")
        return f'<div class="screenshot-placeholder">待补截图：{html.escape(description)}</div>'
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return (
        '<figure class="manual-screenshot">'
        f'<img src="data:{html.escape(mime, quote=True)};base64,{encoded}" alt="{html.escape(description, quote=True)}">'
        f'<figcaption>{html.escape(description)}</figcaption>'
        '</figure>'
    )


def markdown_to_html(
    markdown: str, screenshots_dir: Path, manifest: dict[str, dict[str, Any]], warnings: list[str], section_id: str
) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    code_language: str | None = None
    code_lines: list[str] = []
    heading_counts: dict[str, int] = {}

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markdown(' '.join(item.strip() for item in paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    index = 0
    while index < len(lines):
        line = lines[index]
        fence = FENCE_RE.match(line)
        if code_language is not None:
            if fence:
                language = html.escape(code_language or "text", quote=True)
                output.append(f'<pre data-language="{language}"><code class="language-{language}">{html.escape(chr(10).join(code_lines))}</code></pre>')
                code_language = None
                code_lines = []
            else:
                code_lines.append(line)
            index += 1
            continue
        if fence:
            flush_paragraph()
            close_list()
            code_language = fence.group(1) or "text"
            index += 1
            continue
        screenshot = SCREENSHOT_RE.match(line)
        if screenshot:
            flush_paragraph()
            close_list()
            attributes = dict(ATTR_RE.findall(screenshot.group(1)))
            output.append(screenshot_html(attributes, screenshots_dir, manifest, warnings))
            index += 1
            continue
        heading = HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            title = heading.group(2)
            base = safe_identifier(re.sub(r"[`*_]", "", title), f"heading-{index + 1}")
            heading_counts[base] = heading_counts.get(base, 0) + 1
            suffix = "" if heading_counts[base] == 1 else f"-{heading_counts[base]}"
            anchor = f"{section_id}-{base}{suffix}"
            output.append(f'<h{level} id="{html.escape(anchor, quote=True)}">{inline_markdown(title)}</h{level}>')
            index += 1
            continue
        if "|" in line and index + 1 < len(lines) and is_table_separator(lines[index + 1]):
            flush_paragraph()
            close_list()
            headers = split_table_row(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(split_table_row(lines[index]))
                index += 1
            output.append("<div class=\"table-wrap\"><table><thead><tr>" + "".join(f"<th>{inline_markdown(cell)}</th>" for cell in headers) + "</tr></thead><tbody>")
            for row in rows:
                padded = row + [""] * max(0, len(headers) - len(row))
                output.append("<tr>" + "".join(f"<td>{inline_markdown(cell)}</td>" for cell in padded[:len(headers)]) + "</tr>")
            output.append("</tbody></table></div>")
            continue
        list_match = LIST_RE.match(line)
        if list_match:
            flush_paragraph()
            current_type = "ol" if list_match.group(1)[0].isdigit() else "ul"
            if list_type != current_type:
                close_list()
                list_type = current_type
                output.append(f"<{list_type}>")
            output.append(f"<li>{inline_markdown(list_match.group(2))}</li>")
            index += 1
            continue
        if line.startswith(">"):
            flush_paragraph()
            close_list()
            output.append(f"<blockquote>{inline_markdown(line.lstrip('> ').strip())}</blockquote>")
            index += 1
            continue
        if not line.strip():
            flush_paragraph()
            close_list()
            index += 1
            continue
        if list_type:
            close_list()
        paragraph.append(line)
        index += 1

    if code_language is not None:
        warnings.append(f"unclosed code fence in section {section_id}")
        language = html.escape(code_language or "text", quote=True)
        output.append(f'<pre data-language="{language}"><code class="language-{language}">{html.escape(chr(10).join(code_lines))}</code></pre>')
    flush_paragraph()
    close_list()
    return "\n".join(output)


def infer_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return re.sub(r"[`*_]", "", match.group(2)).strip()
    return fallback


def strip_markdown(markdown: str) -> str:
    text = re.sub(r"<!--\s*SCREENSHOT:.*?-->", " ", markdown, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[#>*_`\[\]()|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:6000]


def load_sections(config: dict[str, Any], directory: Path) -> list[dict[str, Any]]:
    configured = config.get("sections")
    sections: list[dict[str, Any]] = []
    if isinstance(configured, list) and configured:
        for index, item in enumerate(configured, start=1):
            if not isinstance(item, dict) or not item.get("file"):
                continue
            section = dict(item)
            section.setdefault("id", f"section-{index}")
            section.setdefault("group", "手册")
            section.setdefault("tags", [section.get("tag", section["group"])])
            sections.append(section)
        return sections
    for index, path in enumerate(sorted(directory.glob("*.md")), start=1):
        markdown = path.read_text(encoding="utf-8")
        sections.append({
            "id": safe_identifier(path.stem.removeprefix("section-"), f"section-{index}"),
            "title": infer_title(markdown, path.stem),
            "group": "手册",
            "tags": ["manual"],
            "file": path.name,
        })
    return sections


def main() -> int:
    args = parse_args()
    work_dir = args.work_dir.expanduser().resolve()
    skill_dir = (args.skill_dir or Path(__file__).resolve().parent.parent).expanduser().resolve()
    config_path = (args.config or work_dir / "manual-config.json").expanduser().resolve()
    sections_dir = (args.sections_dir or work_dir / "sections").expanduser().resolve()
    screenshots_dir = (args.screenshots_dir or work_dir / "screenshots").expanduser().resolve()
    if not config_path.is_file():
        print(f"error: config not found: {config_path}", file=sys.stderr)
        return 2
    if not sections_dir.is_dir():
        print(f"error: sections directory not found: {sections_dir}", file=sys.stderr)
        return 2
    try:
        config = read_json(config_path, {})
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(config, dict):
        print("error: manual config must be a JSON object", file=sys.stderr)
        return 2

    software = config.get("software") if isinstance(config.get("software"), dict) else {}
    name = str(software.get("name") or "Software Manual")
    version = str(software.get("version") or "")
    language = str(software.get("language") or "zh-CN")
    if not re.fullmatch(r"[A-Za-z0-9-]+", language):
        language = "zh-CN"
    output_config = config.get("output") if isinstance(config.get("output"), dict) else {}
    filename = Path(str(output_config.get("filename") or f"{name}-使用手册.html")).name
    output_path = (args.output.expanduser().resolve() if args.output else work_dir / filename)
    if output_path.exists() and not args.force:
        print(f"error: output exists; use --force to replace it: {output_path}", file=sys.stderr)
        return 2

    template_path = skill_dir / "assets" / "docsify-shell.html"
    css_path = skill_dir / "assets" / "docsify-base.css"
    if not template_path.is_file() or not css_path.is_file():
        print(f"error: skill assets missing under {skill_dir / 'assets'}", file=sys.stderr)
        return 2
    template = template_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    manifest = load_screenshot_manifest(screenshots_dir)
    sections = load_sections(config, sections_dir)
    if not sections:
        print("error: no Markdown sections found", file=sys.stderr)
        return 3

    warnings: list[str] = []
    rendered_sections: list[str] = []
    search_index: list[dict[str, Any]] = []
    groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    all_tags: list[str] = []
    used_ids: set[str] = set()
    for index, section in enumerate(sections, start=1):
        filename = str(section.get("file", ""))
        path = sections_dir / filename
        if not path.is_file():
            print(f"error: configured section not found: {path}", file=sys.stderr)
            return 3
        markdown = path.read_text(encoding="utf-8")
        section_id = safe_identifier(str(section.get("id", "")), f"section-{index}")
        if section_id in used_ids:
            print(f"error: duplicate section id: {section_id}", file=sys.stderr)
            return 3
        used_ids.add(section_id)
        title = str(section.get("title") or infer_title(markdown, path.stem))
        group = str(section.get("group") or "手册")
        raw_tags = section.get("tags") or [section.get("tag") or group]
        tags = [str(tag) for tag in raw_tags if str(tag).strip()]
        all_tags.extend(tag for tag in tags if tag not in all_tags)
        body = markdown_to_html(markdown, screenshots_dir, manifest, warnings, section_id)
        rendered_sections.append(
            f'<article class="content-section" id="section-{html.escape(section_id, quote=True)}" '
            f'data-section="{html.escape(section_id, quote=True)}" data-title="{html.escape(title, quote=True)}" '
            f'data-tags="{html.escape(" ".join(tags), quote=True)}" hidden>'
            '<div class="section-toolbar"><button class="section-collapse" type="button" aria-expanded="true">收起内容</button></div>'
            f'<div class="section-body">{body}</div></article>'
        )
        entry = {"id": section_id, "title": title, "group": group, "tags": tags, "body": strip_markdown(markdown)}
        search_index.append(entry)
        groups.setdefault(group, []).append(entry)

    nav_parts: list[str] = []
    for group, entries in groups.items():
        nav_parts.append(
            '<section class="nav-group"><div class="nav-group-header">'
            '<button class="nav-group-toggle" type="button" aria-expanded="true" aria-label="折叠分组"></button>'
            f'<span>{html.escape(group)}</span></div><div class="nav-group-items">'
        )
        for entry in entries:
            nav_parts.append(
                f'<a class="nav-item" href="#/{html.escape(entry["id"], quote=True)}" '
                f'data-section="{html.escape(entry["id"], quote=True)}">{html.escape(entry["title"])}</a>'
            )
        nav_parts.append("</div></section>")

    tag_parts = ['<button class="tag-button" type="button" data-tag="all" aria-pressed="true">全部</button>']
    for tag in all_tags:
        tag_parts.append(
            f'<button class="tag-button" type="button" data-tag="{html.escape(tag, quote=True)}" aria-pressed="false">{html.escape(tag)}</button>'
        )
    search_json = json.dumps(search_index, ensure_ascii=False).replace("</", "<\\/")
    title_json = json.dumps(name, ensure_ascii=False).replace("</", "<\\/")
    replacements = {
        "{{LANG}}": html.escape(language, quote=True),
        "{{TITLE}}": html.escape(name),
        "{{TITLE_JSON}}": title_json,
        "{{VERSION}}": html.escape(version),
        "{{CSS}}": css,
        "{{TAGS}}": "".join(tag_parts),
        "{{NAV}}": "".join(nav_parts),
        "{{SECTIONS}}": "\n".join(rendered_sections),
        "{{SEARCH_INDEX}}": search_json,
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+}}", result)))
    if unresolved:
        print(f"error: unresolved template placeholders: {', '.join(unresolved)}", file=sys.stderr)
        return 3
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    size_bytes = output_path.stat().st_size
    max_size_mb = float(output_config.get("max_size_mb", 20))
    if size_bytes > max_size_mb * 1024 * 1024:
        warnings.append(f"output exceeds configured size limit of {max_size_mb:g} MB")
    report = {
        "status": "completed_with_warnings" if warnings else "completed",
        "output_file": str(output_path),
        "size_bytes": size_bytes,
        "sections": len(sections),
        "screenshots_embedded": result.count('class="manual-screenshot"'),
        "warnings": warnings,
        "offline": True,
    }
    (work_dir / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
