#!/usr/bin/env python3
"""Extract API evidence without installing dependencies or importing the app."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
SPEC_NAMES = {
    "openapi.json", "openapi.yaml", "openapi.yml",
    "swagger.json", "swagger.yaml", "swagger.yml",
}
SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", "node_modules", "vendor",
    "dist", "build", "coverage", ".next", ".nuxt", "target", ".venv",
    "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx"}


@dataclass
class RouteEvidence:
    method: str
    path: str
    source: str
    line: int
    detector: str
    confidence: str = "heuristic"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract OpenAPI summaries and source-derived route evidence safely."
    )
    parser.add_argument("--project", required=True, type=Path, help="Project root to inspect")
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    parser.add_argument(
        "--spec", action="append", default=[], type=Path,
        help="Explicit OpenAPI/Swagger JSON or YAML path; repeat as needed",
    )
    parser.add_argument("--no-source-scan", action="store_true", help="Skip heuristic source route scan")
    parser.add_argument("--require-api", action="store_true", help="Exit non-zero when no API evidence is found")
    parser.add_argument("--max-files", type=int, default=10000, help="Maximum source/spec files to inspect")
    return parser.parse_args()


def iter_project_files(root: Path, max_files: int) -> Iterable[Path]:
    count = 0
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        count += 1
        if count > max_files:
            return
        yield path


def load_spec(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"cannot read {path}: {exc}"
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return None, f"invalid JSON {path}: {exc}"
    else:
        try:
            import yaml  # type: ignore
        except ImportError:
            return None, f"YAML preserved but not parsed (PyYAML is not installed): {path}"
        try:
            data = yaml.safe_load(text)
        except Exception as exc:  # parser-specific exception types vary
            return None, f"invalid YAML {path}: {exc}"
    if not isinstance(data, dict) or not (data.get("openapi") or data.get("swagger")):
        return None, f"not an OpenAPI/Swagger document: {path}"
    return data, None


def md_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def schema_label(schema: Any) -> str:
    if not isinstance(schema, dict):
        return "-"
    if "$ref" in schema:
        return str(schema["$ref"]).split("/")[-1]
    if "type" in schema:
        label = str(schema["type"])
        if label == "array":
            return f"array<{schema_label(schema.get('items', {}))}>"
        return label
    if "oneOf" in schema:
        return "oneOf"
    if "anyOf" in schema:
        return "anyOf"
    if "allOf" in schema:
        return "allOf"
    return "object"


def operation_rows(spec: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        path_parameters = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            parameters = [*path_parameters, *(operation.get("parameters") or [])]
            required = [
                f"{item.get('name')}:{item.get('in')}"
                for item in parameters
                if isinstance(item, dict) and item.get("required")
            ]
            request_body = operation.get("requestBody") or {}
            request_types: list[str] = []
            if isinstance(request_body, dict):
                for media, content in (request_body.get("content") or {}).items():
                    if isinstance(content, dict):
                        request_types.append(f"{media}:{schema_label(content.get('schema', {}))}")
            responses = operation.get("responses") or {}
            rows.append({
                "method": method.upper(),
                "path": route,
                "summary": operation.get("summary") or operation.get("operationId") or "-",
                "tags": operation.get("tags") or [],
                "deprecated": bool(operation.get("deprecated")),
                "required_parameters": required,
                "request_body": request_types,
                "responses": sorted(str(code) for code in responses.keys()),
                "security": operation.get("security", spec.get("security", [])),
            })
    return rows


def write_openapi_markdown(spec: dict[str, Any], source: Path, output: Path) -> int:
    info = spec.get("info") or {}
    rows = operation_rows(spec)
    lines = [
        f"# {info.get('title', 'API Reference')}",
        "",
        f"- 规范版本：`{spec.get('openapi') or spec.get('swagger')}`",
        f"- API 版本：`{info.get('version', 'unknown')}`",
        f"- 来源：`{source}`",
        "",
        "## 端点索引",
        "",
        "| Method | Path | Summary | Tags | Deprecated | Required | Responses |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| `{method}` | `{path}` | {summary} | {tags} | {deprecated} | {required} | {responses} |".format(
                method=md_cell(row["method"]), path=md_cell(row["path"]),
                summary=md_cell(row["summary"]), tags=md_cell(", ".join(row["tags"])),
                deprecated="yes" if row["deprecated"] else "no",
                required=md_cell(", ".join(row["required_parameters"])),
                responses=md_cell(", ".join(row["responses"])),
            )
        )
    schemas = (spec.get("components") or {}).get("schemas") or (spec.get("definitions") or {})
    if isinstance(schemas, dict) and schemas:
        lines.extend(["", "## Schema 索引", "", "| Name | Type | Required fields |", "|---|---|---|"])
        for name, schema in schemas.items():
            required = ", ".join(schema.get("required", [])) if isinstance(schema, dict) else ""
            lines.append(f"| `{md_cell(name)}` | {md_cell(schema_label(schema))} | {md_cell(required)} |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


ROUTE_PATTERNS = [
    ("python-decorator", re.compile(r"@(?:[A-Za-z_]\w*\.)*(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)['\"]", re.I)),
    ("express-router", re.compile(r"\b(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)['\"]", re.I)),
    ("nestjs-decorator", re.compile(r"@(Get|Post|Put|Patch|Delete|Options|Head)\(\s*['\"]?([^'\")]*?)['\"]?\s*\)", re.I)),
    ("django-path", re.compile(r"\b(?:path|re_path)\(\s*['\"]([^'\"]+)['\"]")),
]


def scan_source_routes(root: Path, files: Iterable[Path]) -> tuple[list[RouteEvidence], int]:
    routes: list[RouteEvidence] = []
    scanned = 0
    for path in files:
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        relative = str(path.relative_to(root))
        for line_no, line in enumerate(text.splitlines(), start=1):
            for detector, pattern in ROUTE_PATTERNS:
                for match in pattern.finditer(line):
                    if detector == "django-path":
                        method, route = "ROUTE", match.group(1)
                    else:
                        method, route = match.group(1).upper(), match.group(2) or "/"
                    routes.append(RouteEvidence(method, route, relative, line_no, detector))
        if re.search(r"(?:^|/)app/.+/route\.(?:ts|tsx|js|jsx)$", relative):
            methods = re.findall(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\b", text)
            route_part = re.sub(r"^.*?/app/", "", relative)
            route_part = re.sub(r"/route\.(?:ts|tsx|js|jsx)$", "", route_part)
            route_part = re.sub(r"\([^/]+\)/?", "", route_part)
            route_part = re.sub(r"\[([^]]+)\]", r"{\1}", route_part)
            for method in methods:
                line_no = text[: text.find(f"function {method}")].count("\n") + 1
                routes.append(RouteEvidence(method, "/" + route_part.strip("/"), relative, line_no, "next-route"))
    unique: dict[tuple[str, str, str, int], RouteEvidence] = {}
    for route in routes:
        unique[(route.method, route.path, route.source, route.line)] = route
    return sorted(unique.values(), key=lambda item: (item.path, item.method, item.source, item.line)), scanned


def write_route_inventory(routes: list[RouteEvidence], output: Path) -> None:
    lines = [
        "# Source-derived API route inventory",
        "",
        "> These entries are heuristic source evidence, not a runtime contract. Verify framework prefixes, middleware, authentication, and dynamic registration before publishing.",
        "",
        "| Method | Path fragment | Source | Detector | Confidence |",
        "|---|---|---|---|---|",
    ]
    for route in routes:
        lines.append(
            f"| `{md_cell(route.method)}` | `{md_cell(route.path)}` | `{md_cell(route.source)}:{route.line}` | {md_cell(route.detector)} | {route.confidence} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not project.is_dir():
        print(f"error: project directory does not exist: {project}", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)

    project_files = list(iter_project_files(project, args.max_files))
    explicit_specs = [path.expanduser().resolve() for path in args.spec]
    discovered_specs = [path for path in project_files if path.name.lower() in SPEC_NAMES]
    spec_paths: list[Path] = []
    for path in [*explicit_specs, *discovered_specs]:
        if path not in spec_paths:
            spec_paths.append(path)

    report: dict[str, Any] = {
        "project": str(project),
        "output": str(output),
        "status": "completed",
        "specs": [],
        "source_scan": {"enabled": not args.no_source_scan, "scanned_files": 0, "routes": 0},
        "warnings": [],
    }
    total_operations = 0
    for index, spec_path in enumerate(spec_paths, start=1):
        if not spec_path.is_file():
            report["warnings"].append(f"spec not found: {spec_path}")
            continue
        copied = output / f"source-{index}-{spec_path.name}"
        shutil.copy2(spec_path, copied)
        spec, warning = load_spec(spec_path)
        item = {"source": str(spec_path), "copied_to": str(copied), "parsed": spec is not None}
        if warning:
            item["warning"] = warning
            report["warnings"].append(warning)
        if spec is not None:
            md_path = output / f"openapi-reference-{index}.md"
            count = write_openapi_markdown(spec, spec_path, md_path)
            item.update({"operations": count, "markdown": str(md_path)})
            total_operations += count
        report["specs"].append(item)

    routes: list[RouteEvidence] = []
    if not args.no_source_scan:
        routes, scanned = scan_source_routes(project, project_files)
        report["source_scan"].update({"scanned_files": scanned, "routes": len(routes)})
        if routes:
            route_path = output / "source-route-inventory.md"
            write_route_inventory(routes, route_path)
            report["source_scan"]["markdown"] = str(route_path)
            (output / "source-route-inventory.json").write_text(
                json.dumps([asdict(route) for route in routes], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    if total_operations == 0 and not routes:
        report["status"] = "no_api_evidence"
        report["warnings"].append("No OpenAPI operations or source-derived routes were found.")
    (output / "extraction-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": report["status"],
        "specs": len(report["specs"]),
        "openapi_operations": total_operations,
        "source_routes": len(routes),
        "report": str(output / "extraction-report.json"),
    }, ensure_ascii=False))
    if args.require_api and report["status"] == "no_api_evidence":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
