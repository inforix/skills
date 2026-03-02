# Skills Workspace

This repository contains custom local skills used by the agent runtime.

中文版本：`README.zh-CN.md`

## Current Skills

| Skill | Purpose | Main Entry |
| --- | --- | --- |
| `notion-to-weixin` | Fetch a Notion page by title, keep content in Markdown, process images, and publish to Weixin draft via `wxcli`. | `notion-to-weixin/SKILL.md` |
| `obsidian-to-weixin` | Find an Obsidian note, keep Markdown as source, process images, and publish to Weixin draft via `wxcli`. | `obsidian-to-weixin/SKILL.md` |
| `shmtu-word-formatter` | Format text or existing `.docx` into Shanghai Maritime University official document style and output `.docx`. | `shmtu-word-formatter/SKILL.md` |

## Repository Layout

- `notion-to-weixin/`
  - Skill instructions (`SKILL.md`)
  - command references and templates (`references/`)
  - optional styling assets (`assets/`)
- `obsidian-to-weixin/`
  - Skill instructions (`SKILL.md`)
  - command references (`references/`)
  - optional styling assets (`assets/`)
- `shmtu-word-formatter/`
  - Skill instructions (`SKILL.md`)
  - formatter script (`scripts/format_word.py`)
  - formatting spec (`references/format-spec.md`)
- `dist/`
  - generated artifacts/build outputs (if any)

## Notes

- Each skill is self-contained. Start from its `SKILL.md`.
- Follow tool prerequisites in each skill before running commands.
