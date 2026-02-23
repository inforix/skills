---
name: notion-to-weixin
description: Fetch a Notion page by title, export to Markdown, convert Markdown to HTML with a user-provided CSS file, and create a Weixin draft via wxcli. Use when asked to publish Notion content into Weixin draftbox, or when moving Notion pages into Weixin draft as HTML.
---

# Notion to Weixin

## Workflow (Sequential)

1. Resolve Notion page ID from the given title.
2. Export the page to Markdown.
3. Ensure `author` exists in Markdown front matter (and inject a byline if needed).
4. Convert Markdown to HTML (optional; needed for custom CSS).
5. Prepare `thumb_media_id`:
   - If the Notion page has a cover, upload it as a Weixin `thumb` material and use that ID.
   - If no cover, use the last image material ID.
6. Create a new Weixin draft with HTML (manual conversion) or Markdown (wxcli auto-conversion).

## Inputs (Ask the user if missing)

- `notion_title`: exact Notion page title to publish.
- `css_path`: optional local CSS file path to apply during Markdown to HTML conversion. Defaults to `assets/default.css`.
- `author`: default author name (used for Markdown front matter and optional byline).
- `thumb_media_id`: only required if cover and image fallback both fail.

## Prerequisites

- `notion-cli` installed and authenticated (NOTION_TOKEN or `notion auth set`).
- `wxcli` installed and authenticated (`wxcli auth set` or `wxcli auth login`).
- `curl` and `jq` available.
- `npx markdown-to-html-cli` available if using manual HTML conversion.

## Step 1: Resolve Page ID by Title

1. Copy `references/notion-search.json` to a temp file and replace `__TITLE__`.
2. Run `notion search --body @query.json`.
3. Choose the exact-title match. If multiple matches remain, pick the most recently edited or ask the user to confirm.
4. If no match is found, ask for a Notion page ID or URL and extract the ID.

## Step 2: Export Page to Markdown

- Use `notion pages export <page_id> --assets=link -o <workdir>/page.md`.
- Use a workdir like `/tmp/notion-to-weixin/<slug-or-timestamp>`.

## Step 3: Default Author Handling

- Read `<workdir>/page.md` and ensure YAML front matter exists.
- Set or overwrite `author:` in front matter to the chosen author.
- If no front matter exists, insert:

```markdown
---
author: <AUTHOR>
---
```

- If wxcli does not support an author flag, inject a byline in Markdown after front matter:

```markdown
*作者：<AUTHOR>*
```

## Step 4: Convert Markdown to HTML (Optional)

Use manual conversion when you need a specific CSS theme. If your wxcli build supports
Markdown input, you can skip this step and pass Markdown directly in Step 6.

- Convert with the user-provided CSS (or default CSS if none is provided):

```bash
npx markdown-to-html-cli --source <workdir>/page.md --style <css_path> > <workdir>/page.html
```

## Step 5: Prepare `thumb_media_id`

### 5.1 If Notion page has a cover

1. Fetch page metadata:

```bash
curl -sS \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  "https://api.notion.com/v1/pages/<page_id>" > <workdir>/page.json
```

2. Extract cover URL:

```bash
cover_url=$(jq -r '.cover | if .==null then "" elif .type=="external" then .external.url else .file.url end' <workdir>/page.json)
```

3. If `cover_url` is set, download and upload as thumb:

```bash
curl -L "$cover_url" -o <workdir>/cover.jpg
thumb_media_id=$(wxcli material upload --type thumb --file <workdir>/cover.jpg --json | jq -r '.media_id')
```

Note: Notion file URLs expire quickly. If download fails, re-fetch page metadata and retry.

### 5.2 If no cover exists

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

## Step 6: Create Weixin Draft

- Create a new draft using HTML content (manual conversion path):

```bash
wxcli draft add \
  --title "<notion_title>" \
  --content - \
  --thumb-media-id "$thumb_media_id" < <workdir>/page.html
```

- Create a new draft using Markdown content (wxcli auto-conversion path):

```bash
wxcli draft add \
  --title "<notion_title>" \
  --content - \
  --thumb-media-id "$thumb_media_id" < <workdir>/page.md
```

If your wxcli build requires an explicit flag to indicate Markdown input, add it to the command.

- If you need machine-readable output, add `--json` and capture the returned `media_id`.

## Optional: Single-Pipe Draft Creation

If you prefer a single pipe for HTML → draft creation, use this:

```bash
npx markdown-to-html-cli --source <workdir>/page.md --style <css_path> | \
  wxcli draft add --title "<notion_title>" --content - --thumb-media-id "$thumb_media_id"
```

Note: you still need the author/front‑matter step before this pipe.

If you prefer a single pipe for Markdown → draft creation (wxcli auto‑conversion):

```bash
cat <workdir>/page.md | \
  wxcli draft add --title "<notion_title>" --content - --thumb-media-id "$thumb_media_id"
```


## Resources

- `references/notion-search.json`: JSON template for Notion title search.
- `references/cli-commands.md`: Canonical CLI command examples for `notion-cli` and `wxcli`.
- `assets/default.css`: Default CSS theme (used when `css_path` is not provided).

## Scripts

- `scripts/ensure_author.py`: Ensure Markdown front matter has `author`, and optionally inject a byline.

```bash
scripts/ensure_author.py --input <workdir>/page.md --author "NAME" --byline
```

- `scripts/run_pipeline.sh`: One-shot test script for the full Notion → HTML → Weixin flow.

```bash
scripts/run_pipeline.sh --title "My Notion Page" --css /path/style.css --author "NAME"
```

Notes:
- Use `--page-id` if the title search is ambiguous.
- Use `--thumb-media-id` only if cover and image fallback are unavailable.
- The script uses manual HTML conversion to apply CSS. For wxcli auto‑conversion, use the Markdown commands in Step 6.
