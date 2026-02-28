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

## wxcli

Auth:

```bash
wxcli auth set --appid YOUR_APPID --appsecret YOUR_SECRET
wxcli auth login
wxcli auth status --json
```

Upload image material (inline images):

```bash
wxcli material upload --type image --file ./image.png --json
```

Upload thumb material (cover):

```bash
wxcli material upload --type thumb --file ./cover.jpg --json
```

Material count:

```bash
wxcli material count --json
```

List image materials:

```bash
wxcli material list --type image --offset 0 --count 10 --json
```

Create draft from Markdown stdin:

```bash
wxcli draft add --title "Hello" --content - --thumb-media-id MEDIA_ID < article.md
```

Create draft with explicit Markdown + CSS:

```bash
wxcli draft add --title "Hello" --format markdown --css-path ./style.css --content - --thumb-media-id MEDIA_ID < article.md
```
