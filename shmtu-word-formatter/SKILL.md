---
name: shmtu-word-formatter
description: 把文章按“上海海事大学党政公文格式”刷成 Word（.docx），或对已有 .docx 进行统一排版后保存。凡是用户提到“刷格式”“按公文格式排版”“生成 Word”“把这篇文章整理成正式公文格式”“这个 docx 帮我统一格式”时都应触发本技能。
---

# shmtu-word-formatter

用于把文章快速整理为符合上海海事大学党政公文规范的 Word 文档。

## 你要做什么

1. **识别输入类型**：
   - 已有 `.docx`：直接重排版并输出新文件。
   - 纯文本（`.txt/.md` 或用户直接粘贴）：先转为文档，再统一排版。
2. **调用脚本**：`scripts/format_word.py`。
3. **输出结果**：始终产出 `.docx` 文件。
4. **最后提示人工复核**：标题多行形状、附件版式、印章签批等复杂布局。

## 格式标准（执行口径）

详见 `references/format-spec.md`。默认执行为：
- A4
- 标题 2号方正小标宋简体居中
- 正文 3号仿宋
- 层级字体：黑体 / 楷体 / 仿宋
- 日期去零
- 页码 `— PAGE —`

## 使用方式

### 0) 首次使用先安装依赖（仅一次）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r skills/shmtu-word-formatter/scripts/requirements.txt
```

### 1) 已有 Word，直接刷格式

```bash
source .venv/bin/activate
python skills/shmtu-word-formatter/scripts/format_word.py \
  --input ./input.docx \
  --output ./input-格式化.docx
```

### 2) 文本转 Word 并刷格式

```bash
source .venv/bin/activate
python skills/shmtu-word-formatter/scripts/format_word.py \
  --input ./article.txt \
  --output ./article-公文版.docx
```

### 3) 覆盖标题（可选）

```bash
source .venv/bin/activate
python skills/shmtu-word-formatter/scripts/format_word.py \
  --input ./article.docx \
  --output ./article-公文版.docx \
  --title "关于开展春季学期重点工作的通知"
```

## 参数说明

- `--input`：输入文件（`.docx/.txt/.md`）
- `--output`：输出 `.docx`
- `--title`：可选，强制覆盖标题
- `--text`：可选，直接传文本
- `--text-file`：可选，从文本文件读取
- `--no-page-number`：可选，不加页码

## 处理原则

- 默认不覆盖原文件，输出到新文件。
- 若用户明确要求覆盖，先提醒风险再执行。
- 格式冲突时，以本技能规范为准；若用户给出新的明确规范，以用户规范优先。
