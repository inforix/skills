# Swagger/OpenAPI 提取

## 选择方法

1. 优先读取仓库已有 `openapi.json|yaml` 或 `swagger.json|yaml`。
2. 若本地服务已安全运行，可读取项目公开的 `/openapi.json`、`/swagger.json` 等端点。
3. 仅当项目已经配置 `swagger-jsdoc`、Nest Swagger 或其他生成命令时，运行现有命令。
4. 以上均不可用时，使用 `extract_apis.py` 的带证据启发式清单。

不要安装新包，不修改应用以暴露文档端点，不访问生产 Swagger 管理页。

## 检查内容

- `openapi`/`swagger` 版本与 `info.version`。
- `servers`、安全方案和全局安全要求。
- path + method 唯一组合。
- tags、deprecated、参数位置和必填性。
- 请求体、响应状态码、schema 和 examples。
- `$ref` 是否可解析；跨文件引用失败时记录具体路径。

对比生成的端点数量与规范的 path+method 数。不要覆盖原规范或自动“修复”它。
