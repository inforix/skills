# 阶段 5：Word 组装

## 输入

- `manual-config.json`
- `sections/*.md`
- `screenshots/screenshots-manifest.json`（可选）
- `screenshots/*`（可选）

## 执行

先加载 Codex 工作区依赖，使用返回的 Python；不要用系统 Python 临时安装 `python-docx`。

```bash
<bundled-python> <skill-dir>/scripts/assemble_docx.py \
  --work-dir <work-dir> \
  --output <work-dir>/<manual-name>.docx
```

可用参数：`--config`、`--sections-dir`、`--screenshots-dir`、`--output`、`--force`。

组装器采用 `compact_reference_guide` 预设与 `editorial_cover` 封面。Markdown 保持为内容真源，DOCX 为最终可编辑交付。截图标记解析为真实图片、图题与替代文本；缺图时生成醒目的“待补截图”说明并记录 warning，不伪造图片。

## 质量门禁

- 所有配置章节存在且非空。
- 封面包含软件名、版本、手册类型和生成日期。
- 有目录域、稳定的 Heading 1–3、页眉和页码域。
- 列表使用 Word 编号定义，不用手打 `1.` 或 `•`。
- 表格使用固定 DXA 宽度、显式列宽和重复表头，不超过正文宽度。
- 截图宽度受正文区域约束，保持纵横比，具有图题和替代文本。
- 代码块使用等宽字体、浅色底纹，长行按安全边界换行。
- 组装完成后，在渲染运行时显式加载系统字体配置和中文回退字体；不得仅凭 DOCX 内部字体声明判断中文显示正常。
- 文档不包含远程图片、宏、外链模板、DDE 或 OLE 对象。
- `docx-build-report.json` 记录章节数、截图数、表格数、警告和文件大小。
- 超过大小上限时给出警告，不自动降质或删除内容。
