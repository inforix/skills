# CLI Commands (Notion + Weixin)

This file records the canonical command forms used by the skill.
Verify against the upstream READMEs if a command fails.

## notion-cli

Auth:

```bash
notion auth status
notion auth set --token YOUR_TOKEN
```

Search:

```bash
notion search --body @query.json
```

Export page to Markdown:

```bash
notion pages export <page_id> --assets=download -o page.md
```

Download a Notion file object (e.g., cover image):

```bash
notion files read --body @- --output ./cover.jpg
```

## node-wxcli

Install and verify:

```bash
npm install -g node-wxcli
node-wxcli --help
```

Auth:

```bash
node-wxcli auth set --appid YOUR_APPID --appsecret YOUR_SECRET
node-wxcli auth login
node-wxcli auth status --json
```

Upload a thumb material:

```bash
node-wxcli material upload --type thumb --file ./cover.jpg --json
```

Count materials:

```bash
node-wxcli material count --json
```

List image materials:

```bash
node-wxcli material list --type image --offset 0 --count 10 --json
```

Create a draft (Markdown from stdin; required: `--css-path` with `--format markdown`):

```bash
node-wxcli draft add --title "Hello" --format markdown --css-path ./style.css --content - --thumb-media-id MEDIA_ID < article.md
```

Create a draft with the skill default CSS:

```bash
node-wxcli draft add --title "Hello" --format markdown --css-path ./assets/default.css --content - --thumb-media-id MEDIA_ID < article.md
```
