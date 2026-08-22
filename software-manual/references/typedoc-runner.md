# TypeDoc 提取

## 使用条件

仅在 TypeScript 项目已经包含 TypeDoc 及其配置，或 `npx typedoc --version` 能使用本地锁定依赖时执行。不要运行会下载远程包的命令，不要修改 `package.json` 或锁文件。

## 推荐流程

1. 检查 `typedoc.json`、`package.json` scripts、公共入口和导出映射。
2. 先执行项目已有文档脚本；否则使用本地 `node_modules/.bin/typedoc`。
3. 把输出写入工作目录，例如 `<work-dir>/api-docs/typescript/`。
4. 只记录公共导出；排除测试、生成文件和内部模块。
5. 对缺失注释、无法解析的类型或空入口发出 warning。

若 TypeDoc 不可用，直接从 `package.json` exports、入口文件、类型声明、示例和测试建立公共 API 清单，并标记为源码级证据。
