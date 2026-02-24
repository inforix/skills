---
name: notion-to-weixin
description: Fetch a Notion page by title, export to Markdown, convert Markdown to HTML with a user-provided CSS file, and create a Weixin draft via wxcli. Use when asked to publish Notion content into Weixin draftbox, or when moving Notion pages into Weixin draft as HTML.
---

# Notion to Weixin

## Config (Optional)

Set a default `author` in `~/.agents/config.yaml`:

```yaml
notion_to_weixin:
  author: "Alice Wang"
```

You can also set a global default:

```yaml
author: "Alice Wang"
```

## Workflow (Sequential)

1. Resolve Notion page ID from the given title.
2. Export the page to Markdown.
3. Prepare `thumb_media_id`:
   - If the Notion page has a cover, upload it as a Weixin `thumb` material and use that ID.
   - If no cover, use the last image material ID.
4. Create a new Weixin draft using Markdown input (wxcli converts to HTML).

## Inputs (Ask the user if missing)

- `notion_title`: exact Notion page title to publish.
- `thumb_media_id`: only required if cover and image fallback both fail.

## Prerequisites

- `notion-cli` installed and authenticated (NOTION_TOKEN or `notion auth set`).
- `wxcli` installed and authenticated (`wxcli auth set` or `wxcli auth login`).
- `curl` and `jq` available.
- `python3` + `pyyaml` only if you want `.agents/config.yaml` defaults.

## Step 1: Resolve Page ID by Title

1. Copy `references/notion-search.json` to a temp file and replace `__TITLE__`.
2. Run `notion search --body @query.json`.
3. Choose the exact-title match. If multiple matches remain, pick the most recently edited or ask the user to confirm.
4. If no match is found, ask for a Notion page ID or URL and extract the ID.

## Step 2: Export Page to Markdown

- Use `notion pages export <page_id> --assets=link -o <workdir>/page.md`.
- Use a workdir like `/tmp/notion-to-weixin/<slug-or-timestamp>`.

## Step 3: Default Author Handling

- If `author` is not provided, read it from `~/.agents/config.yaml` .



## Step 4: Prepare `thumb_media_id`

### 4.1 If Notion page has a cover

1. Fetch page metadata (use notion-cli):

```bash
notion pages get <page_id> > <workdir>/page.json
```

2. Extract cover type + cover URL:

```bash
cover_type=$(jq -r '.cover.type // ""' <workdir>/page.json)
cover_url=$(jq -r '.cover | if .==null then "" elif .type=="external" then .external.url else .file.url end' <workdir>/page.json)
```

3. If cover type is `file`, download via notion-cli; if `external`, use curl:

```bash
if [ "$cover_type" = "file" ]; then
  jq -c '.cover' <workdir>/page.json | notion files read --body @- --output <workdir>/cover.jpg
else
  curl -L "$cover_url" -o <workdir>/cover.jpg
fi
thumb_media_id=$(wxcli material upload --type thumb --file <workdir>/cover.jpg --json | jq -r '.media_id')
```

Note: Notion file URLs expire quickly. If download fails, re-fetch page metadata and retry.

### 4.2 If no cover exists

1. Get image material count:

```bash
image_count=$(wxcli material count --json | jq -r '.image_count')
```

2. If `image_count > 0`, fetch the last image and use its `media_id`:

```bash
offset=$((image_count - 1))
thumb_media_id=$(wxcli material list --type image --offset "$offset" --count 1 --json | jq -r '.item[0].media_id')
```

3. If no images exist, ask the user to provide a `thumb_media_id` or upload a thumb manually.

## Step 5: Create Weixin Draft (Markdown input)

```bash
wxcli draft add \
  --title "<notion_title>" \
  --author "<author>" \
  --content - \
  --thumb-media-id "$thumb_media_id" < <workdir>/page.md
```

If your wxcli build requires an explicit flag to indicate Markdown input, add it to the command.

Recommended (explicit format):

```bash
wxcli draft add \
  --title "<notion_title>" \
  --author "<author>" \
  --format markdown \
  --content - \
  --thumb-media-id "$thumb_media_id" < <workdir>/page.md
```

- If you need machine-readable output, add `--json` and capture the returned `media_id`.


## Resources

- `references/notion-search.json`: JSON template for Notion title search.
- `references/cli-commands.md`: Canonical CLI command examples for `notion-cli` and `wxcli`.

## Scripts

- `scripts/ensure_author.py`: Ensure Markdown front matter has `author`, and optionally inject a byline.

```bash
scripts/ensure_author.py --input <workdir>/page.md --author "NAME" --byline
```

- `scripts/run_pipeline.sh`: One-shot test script for the full Notion → Weixin flow (Markdown input).

```bash
scripts/run_pipeline.sh --title "My Notion Page" --author "NAME"
```

Notes:
- Use `--page-id` if the title search is ambiguous.
- Use `--thumb-media-id` only if cover and image fallback are unavailable.
- The script uses wxcli Markdown conversion (no manual HTML step).
- If `--author` is omitted, the script attempts to read `.agent/config.yaml` (see Config above).
