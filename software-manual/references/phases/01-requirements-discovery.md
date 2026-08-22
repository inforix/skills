# 阶段 1：需求发现

## 目标

把用户请求和仓库事实整理为唯一的 `manual-config.json`。不要用一长串问题阻塞可以自动完成的工作。

## 执行

1. 读取用户明确指定的语言、受众、范围、模板、版式和输出目录；未指定格式时默认 Word `.docx`。
2. 检查 `package.json`、`pyproject.toml`、`Cargo.toml`、`go.mod`、桌面应用清单、README、现有 docs 和启动脚本。
3. 自动识别软件名称、版本、类型、主要技术栈、是否有 UI/API/CLI、可能的启动命令。
4. 只有以下信息缺失且会改变结果时才提问：目标受众、允许的认证方式、是否可启动服务、明确的产品范围或特殊 Word 模板/版式。不要仅为确认默认格式而提问。
5. 把未确认但风险较低的判断写入 `assumptions`，把明确不做的内容写入 `excluded`。
6. 按 `references/config-schema.md` 写出配置。

## 范围裁剪

- `quick_start`：概述、安装、首个成功任务。
- `user_guide`：任务式操作、界面、常见问题。
- `developer`：架构、API/SDK、示例、扩展点。
- `administrator`：配置、部署、监控、备份、故障恢复。
- `comprehensive`：仅在用户确实需要且仓库可证明时组合以上内容。

## 门禁

- 项目根目录和最终输出目录明确。
- 软件类型与受众明确或已记录假设。
- 配置中 `output.primary_format` 默认为 `docx`，`output.supplemental_formats` 默认包含 `single_html`；PDF 仅在用户明确要求时附加。
- 未把“生成手册”扩展为修改、部署或发布软件。
