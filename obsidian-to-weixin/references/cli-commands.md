# CLI Commands (Obsidian + Weixin)

Canonical command forms for this skill.

## obsidian-cli

Show help:

```bash
obsidian-cli --help
```

Show default vault:

```bash
obsidian-cli print-default
obsidian-cli print-default --path-only
```

Find note by title/keyword:

```bash
obsidian-cli search "Weekly Update"
obsidian-cli search-content "Weekly Update"
```

Print note content (when you already know note name):

```bash
obsidian-cli print "Weekly Update"
```

List vault files/folders:

```bash
obsidian-cli list
obsidian-cli list Projects
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

Upload image material (inline images):

```bash
node-wxcli material upload --type image --file ./image.png --json
```

Upload thumb material (cover):

```bash
node-wxcli material upload --type thumb --file ./cover.jpg --json
```

Material count:

```bash
node-wxcli material count --json
```

List image materials:

```bash
node-wxcli material list --type image --offset 0 --count 10 --json
```

Create draft from Markdown stdin (required: `--css-path` with `--format markdown`):

```bash
node-wxcli draft add --title "Hello" --digest "AI摘要" --format markdown --css-path ./style.css --content - --thumb-media-id MEDIA_ID < article.md
```

Create draft with the skill default CSS:

```bash
node-wxcli draft add --title "Hello" --digest "AI摘要" --format markdown --css-path ./assets/default.css --content - --thumb-media-id MEDIA_ID < article.md
```
