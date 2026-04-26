# Skills Workspace

This repository contains custom local skills used by the agent runtime.

中文版本：`README.zh-CN.md`

## Current Skills

| Skill | Purpose | Main Entry |
| --- | --- | --- |
| `notion-to-weixin` | Fetch a Notion page by title, keep content in Markdown, process images, and publish to Weixin draft via `node-wxcli`. | `notion-to-weixin/SKILL.md` |
| `obsidian-to-weixin` | Find an Obsidian note, keep Markdown as source, process images, and publish to Weixin draft via `node-wxcli`. | `obsidian-to-weixin/SKILL.md` |
| `imagegen` | Generate images with Azure OpenAI GPT-image models and save local image files. | `imagegen/SKILL.md` |
| `shmtu-word-formatter` | Format text or existing `.docx` into Shanghai Maritime University official document style and output `.docx`. | `shmtu-word-formatter/SKILL.md` |
| `electronic-trusted-certificate` | Use an MCP-over-HTTP workflow to probe, discover, and call SHMTU electronic trusted certificate tools with bearer-token auth. | `electronic-trusted-certificate/SKILL.md` |

## Repository Layout

- `notion-to-weixin/`
  - Skill instructions (`SKILL.md`)
  - command references and templates (`references/`)
  - optional styling assets (`assets/`)
- `obsidian-to-weixin/`
  - Skill instructions (`SKILL.md`)
  - command references (`references/`)
  - optional styling assets (`assets/`)
- `imagegen/`
  - Skill instructions (`SKILL.md`)
  - Azure OpenAI image generation CLI (`scripts/generate-image.mjs`)
  - API notes (`references/`)
- `shmtu-word-formatter/`
  - Skill instructions (`SKILL.md`)
  - formatter script (`scripts/format_word.py`)
  - formatting spec (`references/format-spec.md`)
- `electronic-trusted-certificate/`
  - Skill instructions (`SKILL.md`)
  - MCP-over-HTTP helper script (`scripts/http_mcp.mjs`)
- `dist/`
  - generated artifacts/build outputs (if any)

## Notes

- Each skill is self-contained. Start from its `SKILL.md`.
- Follow tool prerequisites in each skill before running commands.
