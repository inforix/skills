#!/usr/bin/env python3
"""Validate software-manual inputs and the assembled offline HTML."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SCREENSHOT_RE = re.compile(r'<!--\s*SCREENSHOT:\s*(.*?)\s*-->')
ATTR_RE = re.compile(r'([A-Za-z_][\w-]*)="([^"]*)"')
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+}}|\[(?:TODO|TBD)[^]]*]", re.I)
SECRET_PATTERNS = {
    "OpenAI-style token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Bearer token": re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}", re.I),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


class ManualHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.section_ids: list[str] = []
        self.images: list[dict[str, str]] = []
        self.external_assets: list[str] = []
        self.has_manual_marker = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if "id" in data:
            self.ids.append(data["id"])
        classes = data.get("class", "").split()
        if tag == "article" and "content-section" in classes:
            self.section_ids.append(data.get("id", ""))
        if tag == "img":
            self.images.append(data)
        if tag == "body" and data.get("data-manual") == "software-manual":
            self.has_manual_marker = True
        if tag == "script" and data.get("src", "").startswith(("http://", "https://", "//")):
            self.external_assets.append(data["src"])
        if tag == "link" and data.get("href", "").startswith(("http://", "https://", "//")):
            self.external_assets.append(data["href"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated software manual artifacts")
    parser.add_argument("--work-dir", required=True, type=Path, help="Manual working directory")
    parser.add_argument("--html", type=Path, help="Assembled HTML path")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_image_file(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 32:
        return False
    header = path.read_bytes()[:16]
    return (
        header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith(b"\xff\xd8\xff")
        or header.startswith((b"GIF87a", b"GIF89a"))
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )


def find_html(work_dir: Path, config: dict[str, Any], explicit: Path | None) -> Path | None:
    if explicit:
        return explicit.expanduser().resolve()
    report_path = work_dir / "build-report.json"
    if report_path.is_file():
        try:
            report = read_json(report_path)
            if report.get("output_file"):
                return Path(report["output_file"]).expanduser().resolve()
        except (OSError, json.JSONDecodeError):
            pass
    output = config.get("output") if isinstance(config.get("output"), dict) else {}
    filename = output.get("filename")
    return work_dir / str(filename) if filename else None


def main() -> int:
    args = parse_args()
    work_dir = args.work_dir.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}

    config_path = work_dir / "manual-config.json"
    if not config_path.is_file():
        errors.append(f"missing config: {config_path}")
        config: dict[str, Any] = {}
    else:
        try:
            config = read_json(config_path)
            if not isinstance(config, dict):
                raise ValueError("root is not an object")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"invalid config: {exc}")
            config = {}

    sections_dir = work_dir / "sections"
    configured_sections = config.get("sections") if isinstance(config.get("sections"), list) else []
    section_paths: list[Path] = []
    if configured_sections:
        seen_ids: set[str] = set()
        for item in configured_sections:
            if not isinstance(item, dict) or not item.get("file"):
                errors.append("configured section is missing file")
                continue
            section_id = str(item.get("id", ""))
            if not section_id:
                errors.append(f"configured section is missing id: {item.get('file')}")
            elif section_id in seen_ids:
                errors.append(f"duplicate configured section id: {section_id}")
            seen_ids.add(section_id)
            section_paths.append(sections_dir / str(item["file"]))
    elif sections_dir.is_dir():
        section_paths = sorted(sections_dir.glob("*.md"))
    if not section_paths:
        errors.append("no Markdown sections found")

    screenshot_ids: list[str] = []
    for path in section_paths:
        if not path.is_file():
            errors.append(f"missing section: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            errors.append(f"empty section: {path.name}")
        if not re.search(r"^#\s+\S", text, re.M):
            warnings.append(f"section has no H1 heading: {path.name}")
        if text.count("```") % 2:
            errors.append(f"unbalanced fenced code block: {path.name}")
        for match in PLACEHOLDER_RE.finditer(text):
            warnings.append(f"placeholder in {path.name}: {match.group(0)[:60]}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"possible {label} in {path.name}")
        for marker in SCREENSHOT_RE.finditer(text):
            attrs = dict(ATTR_RE.findall(marker.group(1)))
            screenshot_id = attrs.get("id", "").strip()
            if not screenshot_id:
                errors.append(f"screenshot marker missing id in {path.name}")
                continue
            if screenshot_id in screenshot_ids:
                errors.append(f"duplicate screenshot id: {screenshot_id}")
            screenshot_ids.append(screenshot_id)
            if not attrs.get("description", "").strip():
                warnings.append(f"screenshot marker missing description: {screenshot_id}")

    screenshots_dir = work_dir / "screenshots"
    manifest_path = screenshots_dir / "screenshots-manifest.json"
    manifest_by_id: dict[str, dict[str, Any]] = {}
    if manifest_path.is_file():
        try:
            manifest = read_json(manifest_path)
            items = manifest.get("screenshots", []) if isinstance(manifest, dict) else manifest
            if not isinstance(items, list):
                raise ValueError("screenshots must be an array")
            for item in items:
                if not isinstance(item, dict) or not item.get("id"):
                    errors.append("invalid screenshot manifest entry")
                    continue
                screenshot_id = str(item["id"])
                if screenshot_id in manifest_by_id:
                    errors.append(f"duplicate screenshot manifest id: {screenshot_id}")
                manifest_by_id[screenshot_id] = item
                if item.get("status") == "captured":
                    image_path = screenshots_dir / str(item.get("file", ""))
                    if not is_image_file(image_path):
                        errors.append(f"captured screenshot is missing or invalid: {screenshot_id}")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"invalid screenshot manifest: {exc}")
    for screenshot_id in screenshot_ids:
        item = manifest_by_id.get(screenshot_id)
        if not item or item.get("status") != "captured":
            warnings.append(f"screenshot not captured: {screenshot_id}")

    html_path = find_html(work_dir, config, args.html)
    if html_path is None or not html_path.is_file():
        errors.append(f"assembled HTML not found: {html_path}")
    else:
        html_text = html_path.read_text(encoding="utf-8", errors="replace")
        parser = ManualHTMLParser()
        try:
            parser.feed(html_text)
        except Exception as exc:
            errors.append(f"HTML parser error: {exc}")
        if not parser.has_manual_marker:
            errors.append("HTML is missing software-manual marker")
        required_ids = {"manual-search", "manual-nav", "manual-content", "theme-toggle"}
        for missing in sorted(required_ids - set(parser.ids)):
            errors.append(f"HTML missing required element id: {missing}")
        duplicate_ids = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
        for value in duplicate_ids:
            errors.append(f"duplicate HTML id: {value}")
        if len(parser.section_ids) != len(section_paths):
            errors.append(f"HTML section count {len(parser.section_ids)} does not match source count {len(section_paths)}")
        if parser.external_assets:
            errors.append("HTML has external runtime assets: " + ", ".join(parser.external_assets))
        for image in parser.images:
            if not image.get("alt", "").strip():
                errors.append("HTML image is missing alt text")
            src = image.get("src", "")
            if not src.startswith("data:image/"):
                warnings.append(f"HTML image is not embedded: {src[:80]}")
        unresolved = sorted(set(PLACEHOLDER_RE.findall(html_text)))
        if unresolved:
            errors.append("HTML contains unresolved placeholders")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(html_text):
                errors.append(f"possible {label} in HTML")
        search_match = re.search(
            r'<script id="manual-search-data" type="application/json">(.*?)</script>', html_text, re.S
        )
        if not search_match:
            errors.append("HTML search index is missing")
        else:
            try:
                search_data = json.loads(search_match.group(1).replace("<\\/", "</"))
                if len(search_data) != len(section_paths):
                    errors.append("search index count does not match section count")
            except json.JSONDecodeError as exc:
                errors.append(f"invalid search index JSON: {exc}")
        metrics["html_size_bytes"] = html_path.stat().st_size
        metrics["html_sections"] = len(parser.section_ids)
        metrics["embedded_images"] = sum(1 for image in parser.images if image.get("src", "").startswith("data:image/"))

    metrics.update({
        "source_sections": len(section_paths),
        "screenshot_markers": len(screenshot_ids),
        "captured_screenshots": sum(1 for item in manifest_by_id.values() if item.get("status") == "captured"),
    })
    report = {
        "status": "failed" if errors else ("passed_with_warnings" if warnings else "passed"),
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
        "browser_validation_required": True,
    }
    report_path = work_dir / "validation-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": len(errors), "warnings": len(warnings), "report": str(report_path)}, ensure_ascii=False))
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
