# 配置与输出契约

`manual-config.json` 是各阶段共享的事实口径。字段可按项目裁剪，但不同 Agent 不得各自猜测同一信息。

```json
{
  "software": {
    "name": "Example App",
    "version": "1.2.0",
    "description": "一句话产品定位",
    "type": "web",
    "language": "zh-CN"
  },
  "project_root": "/absolute/path/to/repo",
  "target_audiences": ["end_users", "administrators", "developers"],
  "scope": ["tutorial", "how_to", "reference", "explanation"],
  "features": {"has_ui": true, "has_api": true, "has_cli": false, "has_configuration": true},
  "run": {"command": "npm run dev", "url": "http://127.0.0.1:3000", "startup_timeout_seconds": 60},
  "screenshots": {"enabled": true, "viewport": {"width": 1440, "height": 900}, "redact": ["email", "token", "student_id"]},
  "sections": [
    {"id": "overview", "title": "产品概述", "group": "入门", "file": "section-overview.md", "start_on_new_page": true},
    {"id": "tasks", "title": "常用操作", "group": "使用指南", "file": "section-tasks.md", "start_on_new_page": true},
    {"id": "reference", "title": "接口参考", "group": "参考", "file": "section-reference.md", "start_on_new_page": true}
  ],
  "output": {
    "primary_format": "docx",
    "filename": "Example-App-使用手册.docx",
    "supplemental_formats": ["single_html"],
    "return_intermediates": false,
    "paper": "letter",
    "design_preset": "compact_reference_guide",
    "cover_pattern": "editorial_cover",
    "cjk_font": null,
    "include_toc": true,
    "include_header": true,
    "include_page_numbers": true,
    "max_size_mb": 50
  },
  "assumptions": [],
  "excluded": []
}
```

软件类型使用 `web`、`cli`、`sdk`、`desktop`、`service` 或 `mixed`。无 UI 时关闭截图；有 UI 时截图默认必做，并应实际启动应用验证目标页面。无 API 时跳过接口提取。`output.primary_format` 默认为 `docx`，`single_html` 默认为附加格式；HTML 不能静默替代 DOCX。

建议工作目录：

```text
work/software-manual-<timestamp>/
├── manual-config.json
├── exploration/
├── api-docs/
├── sections/
├── screenshots/
├── screenshots-list.json
├── agent-results.json
├── consolidation-summary.md
├── docx-build-report.json
├── docx-validation-report.json
├── render/
├── <软件名>-使用手册.docx
└── <软件名>-使用手册.html
```

`screenshots/screenshots-manifest.json`：

```json
{"screenshots": [{"id": "login", "step": "login-01", "file": "login.png", "description": "登录页及身份验证入口", "url": "/login", "selector": "main", "status": "captured"}]}
```

状态可为 `captured`、`failed`、`manual_required` 或 `skipped`。只有 `captured` 可计入截图覆盖率。配置中的文件路径均相对工作目录解析；输出路径不得覆盖产品源码或已有用户文件，除非用户明确允许。
