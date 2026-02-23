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
notion pages export <page_id> --assets=link -o page.md
```

## wxcli

Auth:

```bash
wxcli auth set --appid YOUR_APPID --appsecret YOUR_SECRET
wxcli auth login
wxcli auth status --json
```

Upload a thumb material:

```bash
wxcli material upload --type thumb --file ./cover.jpg --json
```

Count materials:

```bash
wxcli material count --json
```

List image materials:

```bash
wxcli material list --type image --offset 0 --count 10 --json
```

Create a draft (HTML from stdin):

```bash
wxcli draft add --title "Hello" --content - --thumb-media-id MEDIA_ID
```

Markdown to HTML (used before draft add):

```bash
npx markdown-to-html-cli --source article.md --style=./style.css
```
