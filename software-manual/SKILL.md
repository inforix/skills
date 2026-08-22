---
name: software-manual
description: 从真实软件项目生成可编辑、可验证的 Word（.docx）软件手册，包括项目探索、启动开发服务器及必要依赖、浏览器中的人工认证、真实界面截图、API 提取、专业排版和逐页渲染复核。适用于“软件说明书”“用户手册”“操作手册”“管理员手册”“开发者手册”等端到端任务；普通 README 小修、仅写接口清单或只改代码注释时不要触发。凡是需要运行应用、登录后验证页面或生成带真实 UI 证据的手册，都应使用本技能。
---

# Software Manual

把代码、配置、测试、运行界面和现有文档转化为证据充分的软件手册。默认交付可编辑 Word `.docx` 与无 CDN 依赖的单文件 HTML；Word 是主交付物，PDF 仅在用户明确要求时附加。

## 核心约束

- 以仓库和实际运行结果为事实来源；不得凭命名推断未验证的功能、权限、默认值或返回结果。
- 区分“已验证”“源码可证”“推测/待确认”。最终手册不得把推测写成事实。
- 遵守仓库内 `AGENTS.md` 及用户边界。生成手册不授权修改产品代码、安装依赖、提交、推送或部署。
- 不读取或展示真实密钥、令牌、个人信息。配置示例只使用占位值。
- 不自动安装 TypeDoc、pdoc、Swagger、浏览器或 Word 依赖；优先使用 Codex 工作区已提供的运行时。
- 有 UI 的项目必须在安全、依赖可用且用户未禁止运行时启动应用，验证目标业务页面并采集真实截图；仅端口健康或首页 HTTP 200 不算功能验证。
- 有 UI 的项目必须先按 [运行与认证流程](references/runtime-and-auth.md) 盘点并启动开发服务器及其实际需要的依赖组件（例如数据库、缓存、对象存储、后台 worker）；先检查端口和既有进程，只启动缺失组件，并记录每个本次启动进程的 PID、命令和就绪证据。
- 若应用需要登录、SSO、MFA 或其他人工认证，必须在浏览器中打开认证页面，让用户直接在浏览器输入用户名和密码；不得在聊天、终端、脚本、环境文件或日志中索取、代填、读取或保存密码、验证码、令牌或 Cookie。暂停并等待用户完成认证；只有在用户确认或浏览器显示可验证的已登录业务状态后才继续。
- 启动应用前确认命令和端口；只停止本次启动且 PID 明确的进程，不影响共享服务。不得为截图修改认证、环境配置、锁文件或种子数据。
- 截图前清理敏感数据、调试浮层和无关窗口。每张截图必须有图题、正文引用和替代文本。
- 每一个面向用户的操作都必须说明目的、前置条件、操作位置、单一动作、预期结果和失败恢复；核心操作及关键状态尽量配真实截图。截图用于定位和确认，不能替代可执行的文字步骤。
- 工作文件写入用户指定目录；未指定时使用仓库内 `work/software-manual-<timestamp>/`。最终文件写入用户指定位置或 `docs/manual/`，不要散落到仓库根目录。
- 创建或修改 DOCX 时遵循当前环境的 `documents` 技能；先加载工作区依赖，使用其 Python，并在最终交付前渲染和查看每一页。
- Word 组装与渲染前必须显式加载当前系统字体配置及中文字体回退链，不能只依赖 DOCX 内部的字体声明；若出现中文缺字、方框、乱码或异常回退，修正渲染字体配置后重新渲染整份文档，再逐页复核并记录结果。

## 编排方式

主 Agent 负责范围、事实口径、共享配置、合并、Word 组装和最终验收。存在三个以上互不依赖的分析通道且环境支持时，可用子智能体并行完成探索或章节初稿；每个子智能体只能写自己的输出文件，并仅返回路径、状态、关键发现和阻塞项。不要为很小的项目强行并行。

推荐并行通道：架构与快速入门；界面与用户任务；API/SDK/CLI；配置与运维；故障排查；示例工作流。

## 工作流

### 1. 确定范围

读取 [阶段 1](references/phases/01-requirements-discovery.md)。优先从仓库识别软件名称、版本、类型、读者、启动方式和交付范围。只有缺失信息会实质改变结果时才提问；否则记录合理假设。生成 `manual-config.json`，默认 `output.primary_format` 为 `docx`，并在 `output.supplemental_formats` 中启用 `single_html`。

### 2. 探索项目

执行 [阶段 2](references/phases/02-project-exploration.md)。用 `rg --files`、`rg`、清单文件、路由、schema 和测试建立证据索引，输出 `exploration/*.json`。先读，不修改产品代码。

### 3. 提取接口

项目存在 HTTP API、SDK、公共函数或 CLI 时，执行 [阶段 2.5](references/phases/02.5-api-extraction.md)。先运行安全的静态提取器：

```bash
python <skill-dir>/scripts/extract_apis.py \
  --project <repo-root> \
  --output <work-dir>/api-docs
```

只有在项目已安装对应工具时才按 [Swagger/OpenAPI](references/swagger-runner.md) 或 [TypeDoc](references/typedoc-runner.md) 补充生成。现有 OpenAPI 描述优先于启发式源码扫描。

### 4. 撰写章节

执行 [阶段 3](references/phases/03-parallel-analysis.md)。按软件类型选择章节，不机械生成空章节。采用教程、操作指南、参考和解释四类内容，以目标用户任务为目录主线。每个章节保留事实来源清单。

需要截图的位置使用以下标记，不要伪造图片；`step` 用于把截图绑定到具体操作：

```html
<!-- SCREENSHOT: id="login" step="login-01" url="/login" selector="main" description="登录页及身份验证入口" -->
```

### 5. 合并与质量门禁

执行 [阶段 3.5](references/phases/03.5-consolidation.md)。统一术语、版本、导航、交叉引用和难度层级，生成 `screenshots-list.json`。若仍有事实错误、关键章节缺失或无法解释的冲突，不进入组装阶段。

### 6. 捕获截图

存在 UI 时，先执行 [运行与认证流程](references/runtime-and-auth.md)，再执行 [阶段 4](references/phases/04-screenshot-capture.md) 与 [截图规范](references/screenshot-helper.md)。优先使用 Codex 可用的浏览器控制能力；应用及依赖就绪后逐个验证目标业务页面与关键控件，再采集真实截图。只有无 UI、用户明确禁止运行、依赖确实缺失或用户未完成认证时才能降级；此时生成 `screenshots/MANUAL_CAPTURE.md` 并把交付标记为部分完成，不得把占位图当作真实截图。

### 7. 组装 Word

先加载 Codex 工作区依赖，并使用返回的 Python。然后执行 [阶段 5](references/phases/05-word-assembly.md) 与 [Word 版式规范](references/word-layout.md)：

```bash
<bundled-python> <skill-dir>/scripts/assemble_docx.py \
  --work-dir <work-dir> \
  --output <work-dir>/<manual-name>.docx
```

组装器读取 `manual-config.json`、`sections/*.md` 和截图清单，生成带封面、目录域、标题层级、页眉页脚、图题、表题、代码块和真实列表的可编辑 DOCX，并写入 `docx-build-report.json`。

### 8. 验证和迭代

先运行结构验证：

```bash
<bundled-python> <skill-dir>/scripts/validate_docx.py \
  --docx <work-dir>/<manual-name>.docx \
  --config <work-dir>/manual-config.json \
  --report <work-dir>/docx-validation-report.json
```

再按 [阶段 6](references/phases/06-iterative-refinement.md) 显式加载系统字体配置后，使用 `documents` 技能提供的 `render_docx.py` 把整份 Word 渲染为逐页 PNG，并查看每一页。修复中文字体、遮挡、截断、孤行标题、表格越界、图片失真、页眉页脚冲突和异常空白后，必须重新渲染整份文档。未完成逐页视觉复核时，不得声称 Word 手册已验收。

### 9. 组装单文件 HTML

Word 验收通过后，执行 [HTML 组装阶段](references/phases/05-html-assembly.md)：

```bash
<bundled-python> <skill-dir>/scripts/assemble_docsify.py \
  --work-dir <work-dir> \
  --skill-dir <skill-dir>
```

HTML 与 Word 必须复用同一组 Markdown 章节和真实截图；不得产生两个事实口径。用浏览器验证导航、搜索、主题、图片、窄屏、打印和断网阅读。

## 交付清单

默认向用户交付最终可编辑 Word `.docx`、离线单文件 `.html` 和简短说明。Markdown 源章节、截图原图、构建/验证报告属于中间与 QA 产物；只有用户明确要求时才附带。PDF 可作为固定版式预览，但不能替代 DOCX。

完整字段见 [配置与输出契约](references/config-schema.md)，写作与评分标准见 [写作和质量规范](references/writing-and-quality.md)。评测本技能时使用 [前向测试场景](references/qa-scenarios.md)。方法来源见 [来源说明](references/provenance.md)。
