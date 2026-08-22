# 阶段 5b：单文件 HTML 组装

Word 是主交付物；HTML 使用同一组 `sections/*.md` 与 `screenshots/` 作为附加交付，不能重新发明内容。

```bash
<bundled-python> <skill-dir>/scripts/assemble_docsify.py \
  --work-dir <work-dir> \
  --skill-dir <skill-dir>
```

生成结果必须把 CSS、JavaScript 和真实截图内嵌到单个 HTML，不依赖 CDN、网络字体或远程图片。组装后用浏览器验证侧栏、搜索、主题切换、键盘焦点、图片、窄屏、打印和断网打开。Word 与 HTML 的软件名、版本、章节顺序、API 内容、截图及未验证声明必须一致。
