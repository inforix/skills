#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_pipeline.sh --title "Notion Title" --css /path/style.css --author "Name" [--page-id PAGE_ID] [--workdir DIR] [--thumb-media-id ID]

Requires:
  notion-cli, wxcli, jq, curl, npx (markdown-to-html-cli)
USAGE
}

NOTION_TITLE=""
PAGE_ID=""
CSS_PATH=""
AUTHOR=""
WORKDIR=""
FALLBACK_THUMB_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)
      NOTION_TITLE="$2"; shift 2;;
    --page-id)
      PAGE_ID="$2"; shift 2;;
    --css)
      CSS_PATH="$2"; shift 2;;
    --author)
      AUTHOR="$2"; shift 2;;
    --workdir)
      WORKDIR="$2"; shift 2;;
    --thumb-media-id)
      FALLBACK_THUMB_ID="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "$NOTION_TITLE" && -z "$PAGE_ID" ]]; then
  echo "Missing --title or --page-id"; exit 1
fi
if [[ -z "$AUTHOR" ]]; then
  echo "Missing --author"; exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_CSS="$SCRIPT_DIR/../assets/default.css"
if [[ -z "$CSS_PATH" ]]; then
  CSS_PATH="$DEFAULT_CSS"
fi
if [[ ! -f "$CSS_PATH" ]]; then
  echo "CSS file not found: $CSS_PATH"; exit 1
fi

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="/tmp/notion-to-weixin/$(date +%Y%m%d%H%M%S)"
fi
mkdir -p "$WORKDIR"

if [[ -z "$PAGE_ID" ]]; then
  QUERY_JSON="$WORKDIR/query.json"
  python3 - <<PY
import json
from pathlib import Path

data = Path("/Users/wyp/develop/skills/notion-to-weixin/references/notion-search.json").read_text(encoding="utf-8")
data = data.replace("__TITLE__", "${NOTION_TITLE}")
Path("$QUERY_JSON").write_text(data, encoding="utf-8")
PY

  SEARCH_JSON="$WORKDIR/search.json"
  notion search --body "@$QUERY_JSON" > "$SEARCH_JSON"

  PAGE_ID=$(jq -r --arg title "$NOTION_TITLE" '
    def page_title:
      (.properties // {} | to_entries[]? | select(.value.type=="title") | .value.title | map(.plain_text) | join("")) // "";
    [ .results[] | select(.object=="page") | {id, title: page_title} ] as $pages
    | ($pages | map(select(.title==$title)) | .[0].id)
      // ($pages | .[0].id)
      // empty
  ' "$SEARCH_JSON")

  if [[ -z "$PAGE_ID" ]]; then
    echo "Failed to resolve page ID from title. Provide --page-id."; exit 1
  fi
fi

echo "Using page ID: $PAGE_ID"

notion pages export "$PAGE_ID" --assets=link -o "$WORKDIR/page.md"

/Users/wyp/develop/skills/notion-to-weixin/scripts/ensure_author.py \
  --input "$WORKDIR/page.md" \
  --author "$AUTHOR" \
  --byline

npx markdown-to-html-cli --source "$WORKDIR/page.md" --style "$CSS_PATH" > "$WORKDIR/page.html"

THUMB_MEDIA_ID=""

if [[ -n "${NOTION_TOKEN:-}" ]]; then
  curl -sS \
    -H "Authorization: Bearer $NOTION_TOKEN" \
    -H "Notion-Version: 2022-06-28" \
    "https://api.notion.com/v1/pages/$PAGE_ID" > "$WORKDIR/page.json"

  COVER_URL=$(jq -r '.cover | if .==null then "" elif .type=="external" then .external.url else .file.url end' "$WORKDIR/page.json")
  if [[ -n "$COVER_URL" ]]; then
    curl -L "$COVER_URL" -o "$WORKDIR/cover.jpg"
    THUMB_MEDIA_ID=$(wxcli material upload --type thumb --file "$WORKDIR/cover.jpg" --json | jq -r '.media_id')
  fi
fi

if [[ -z "$THUMB_MEDIA_ID" ]]; then
  IMAGE_COUNT=$(wxcli material count --json | jq -r '.image_count')
  if [[ "$IMAGE_COUNT" -gt 0 ]]; then
    OFFSET=$((IMAGE_COUNT - 1))
    THUMB_MEDIA_ID=$(wxcli material list --type image --offset "$OFFSET" --count 1 --json | jq -r '.item[0].media_id')
  fi
fi

if [[ -z "$THUMB_MEDIA_ID" ]]; then
  THUMB_MEDIA_ID="$FALLBACK_THUMB_ID"
fi

if [[ -z "$THUMB_MEDIA_ID" ]]; then
  echo "No thumb_media_id available. Provide --thumb-media-id or upload a thumb."; exit 1
fi

wxcli draft add \
  --title "$NOTION_TITLE" \
  --content - \
  --thumb-media-id "$THUMB_MEDIA_ID" < "$WORKDIR/page.html"

echo "Draft created. Workdir: $WORKDIR"
