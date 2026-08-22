# 来源说明

本技能以以下方法为基础，并针对 Codex 的技能格式、工具边界和协作模型重新设计：

- `catlog22/Claude-Code-Workflow` 历史 npm 包中的 `.claude/skills/software-manual`。保留“需求 → 探索 → API → 并行撰写 → 整合 → 截图 → 组装 → 迭代”的核心流程，并把默认交付重构为 Word `.docx`；移除 Claude 专属 `Task`、`AskUserQuestion`、Chrome MCP 名称、Windows 硬编码路径和自动安装依赖行为。
- Diátaxis：使用教程、操作指南、参考和解释四种用户需求组织文档。
- Google Developer Documentation Style Guide：使用动作导向步骤、清晰术语、可访问标题、替代文本和非视觉性说明。
- OpenAPI Specification：优先把 OpenAPI 描述作为 HTTP API 的结构化事实来源。
- Playwright 截图实践：区分页面截图、全页截图和元素截图，并在稳定的同一环境中采集。
- Codex `documents` 技能：使用固定设计预设、真实 Word 结构、逐页渲染和视觉复核完成 DOCX 验收。

原项目地址：https://github.com/catlog22/Claude-Code-Workflow

改编内容保留原项目 MIT 许可声明，见技能根目录 `LICENSE.upstream`。

方法参考：

- https://diataxis.fr/
- https://developers.google.com/style/
- https://spec.openapis.org/oas/latest.html
- https://playwright.dev/docs/screenshots

本技能中的 Word 组装与校验脚本为面向 Codex 的重新实现，不依赖原项目的运行时代码。HTML 组装器用于默认附加的离线单文件输出，并与 Word 共用同一内容和截图来源。
