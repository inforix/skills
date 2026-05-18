# Skills 工作区

该仓库用于存放本地自定义 Skills，供代理运行时调用。

English version: `README.md`

## 当前 Skills

| Skill | 用途 | 入口文件 |
| --- | --- | --- |
| `notion-to-weixin` | 按标题获取 Notion 页面，保留 Markdown 内容，处理图片后通过 `node-wxcli` 发布到微信草稿箱。 | `notion-to-weixin/SKILL.md` |
| `obsidian-to-weixin` | 定位 Obsidian 笔记，保留 Markdown 内容，处理图片后通过 `node-wxcli` 发布到微信草稿箱。 | `obsidian-to-weixin/SKILL.md` |
| `imagegen` | 使用 Azure OpenAI GPT-image 模型生成图片并保存到本地。 | `imagegen/SKILL.md` |
| `read-article` | 解读 URL 或本地文件，并在 Obsidian reader vault 中维护可积累的阅读笔记。 | `read-article/SKILL.md` |
| `shmtu-word-formatter` | 将文本或已有 `.docx` 按上海海事大学党政公文规范统一排版并输出 `.docx`。 | `shmtu-word-formatter/SKILL.md` |
| `electronic-trusted-certificate` | 通过 MCP over HTTP 探测、发现并调用上海海事大学电子可信证明相关工具，使用 Bearer Token 鉴权。 | `electronic-trusted-certificate/SKILL.md` |

## 仓库结构

- `notion-to-weixin/`
  - Skill 说明（`SKILL.md`）
  - 命令参考与模板（`references/`）
  - 可选样式资源（`assets/`）
- `obsidian-to-weixin/`
  - Skill 说明（`SKILL.md`）
  - 命令参考（`references/`）
  - 可选样式资源（`assets/`）
- `imagegen/`
  - Skill 说明（`SKILL.md`）
  - Azure OpenAI 图片生成 CLI（`scripts/generate-image.mjs`）
  - API 说明（`references/`）
- `read-article/`
  - Skill 说明（`SKILL.md`）
  - reader vault 辅助 CLI（`scripts/reader-vault.mjs`）
  - wiki 方法与来源笔记模板（`references/`）
- `shmtu-word-formatter/`
  - Skill 说明（`SKILL.md`）
  - 排版脚本（`scripts/format_word.py`）
  - 格式规范（`references/format-spec.md`）
- `electronic-trusted-certificate/`
  - Skill 说明（`SKILL.md`）
  - MCP over HTTP 辅助脚本（`scripts/http_mcp.mjs`）
- `dist/`
  - 构建产物或生成文件（如有）

## 说明

- 每个 Skill 都是独立的，建议从对应 `SKILL.md` 开始阅读。
- 执行命令前请先确认该 Skill 的依赖与前置条件。
